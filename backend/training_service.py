import os
import sys
import argparse
import torch
import numpy as np
import evaluate
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, TextDataset, DataCollatorForLanguageModeling, TrainerCallback
from app import create_app
from models import db, TrainingJob, LLMModel, Dataset

# --- Custom Callback to save metrics ---
class MetricsLoggerCallback(TrainerCallback):
    def __init__(self, job_id):
        self.job_id = job_id

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None:
            job = TrainingJob.query.get(self.job_id)
            if job:
                if job.metrics is None:
                    job.metrics = []
                current_metrics = list(job.metrics)
                current_metrics.append(logs)
                job.metrics = current_metrics
                job.logs += str(logs) + '\n'
                db.session.commit()

# --- Metrics Computation Function ---
accuracy_metric = evaluate.load("accuracy")
perplexity_metric = evaluate.load("perplexity")

def compute_metrics(eval_preds):
    logits, labels = eval_preds
    predictions = np.argmax(logits, axis=-1)
    true_predictions = predictions[labels != -100]
    true_labels = labels[labels != -100]
    accuracy = accuracy_metric.compute(predictions=true_predictions, references=true_labels)
    try:
        perplexity = perplexity_metric.compute(model_id='gpt2', predictions=logits)
    except Exception:
        perplexity = {"perplexity": -1.0}
    return {"accuracy": accuracy.get('accuracy', -1.0), "perplexity": perplexity.get('perplexity', -1.0)}

# --- Main Training Function ---
def run_training(args):
    app = create_app()
    with app.app_context():
        job = TrainingJob.query.get(args.job_id)
        if not job:
            print(f"Error: Training job with ID {args.job_id} not found.")
            return

        try:
            job.status = 'running'
            job.logs = 'Training started...\n'
            db.session.commit()

            print(f"Starting training for job {args.job_id}...")

            base_model_path = job.model.path
            tokenizer = AutoTokenizer.from_pretrained(base_model_path)
            model = AutoModelForCausalLM.from_pretrained(base_model_path)

            if tokenizer.pad_token is None:
                tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                model.resize_token_embeddings(len(tokenizer))

            train_dataset = TextDataset(tokenizer=tokenizer, file_path=job.dataset.path, block_size=128)
            data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

            eval_dataset = None
            if args.eval_dataset_id:
                eval_record = Dataset.query.get(args.eval_dataset_id)
                if eval_record:
                    eval_dataset = TextDataset(tokenizer=tokenizer, file_path=eval_record.path, block_size=128)

            output_dir = os.path.join(os.path.dirname(__file__), 'models', f"{job.model.name}_finetuned_job_{job.id}")

            training_args = TrainingArguments(
                output_dir=output_dir,
                overwrite_output_dir=True,
                num_train_epochs=args.num_train_epochs,
                per_device_train_batch_size=args.per_device_train_batch_size,
                save_steps=10_000,
                save_total_limit=2,
                logging_strategy="epoch",
                evaluation_strategy="epoch" if eval_dataset else "no",
            )

            metrics_callback = MetricsLoggerCallback(job_id=args.job_id)

            trainer = Trainer(
                model=model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                callbacks=[metrics_callback],
                compute_metrics=compute_metrics,
            )

            trainer.train()
            trainer.save_model(output_dir)

            job.status = 'completed'
            job.logs += f"Training finished successfully. Model saved to {output_dir}\n"
            job.completed_at = db.func.now()
            db.session.commit()

        except Exception as e:
            print(f"Error during training job {args.job_id}: {e}")
            job.status = 'failed'
            job.logs += f"\n\nERROR: {e}\n"
            db.session.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a training job.")
    parser.add_argument("job_id", type=int, help="The ID of the training job.")
    parser.add_argument("--eval_dataset_id", type=int, default=None, help="Optional ID of the evaluation dataset.")
    parser.add_argument("--num_train_epochs", type=int, default=1, help="Number of training epochs.")
    parser.add_argument("--per_device_train_batch_size", type=int, default=1, help="Batch size for training.")

    args = parser.parse_args()
    run_training(args)
