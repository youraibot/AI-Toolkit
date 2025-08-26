import os
import torch
from huggingface_hub import HfApi, snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer
from .models import db, LLMModel

# --- Configuration ---
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# --- In-memory cache for loaded models ---
model_cache = {
    "model_id": None,
    "model": None,
    "tokenizer": None,
    "device": "cuda" if torch.cuda.is_available() else "cpu"
}

def search_huggingface_models(query: str, limit: int = 20):
    """Searches the Hugging Face Hub for models."""
    api = HfApi()
    models = api.list_models(search=query, sort='downloads', direction=-1, limit=limit)
    return [{"id": model.modelId, "name": model.modelId, "author": model.author} for model in models]

def list_local_models():
    """Lists all models available in the local database."""
    return LLMModel.query.all()

def download_model(model_id: str):
    """
    Downloads a model from Hugging Face Hub, saves it locally,
    and adds its metadata to the database.
    """
    if LLMModel.query.filter_by(huggingface_id=model_id).first():
        raise ValueError(f"Model '{model_id}' is already downloaded.")

    local_model_name = model_id.replace('/', '_')
    model_path = os.path.join(MODELS_DIR, local_model_name)

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=model_path,
            local_dir_use_symlinks=False
        )
    except Exception as e:
        raise IOError(f"Failed to download model '{model_id}': {e}") from e

    new_model = LLMModel(
        name=local_model_name,
        huggingface_id=model_id,
        status='available',
        path=model_path
    )
    db.session.add(new_model)
    db.session.commit()

    return new_model

def load_model(model_id: int):
    """
    Loads a model into the in-memory cache.
    Only one model can be loaded at a time.
    """
    if model_cache["model_id"] == model_id:
        return

    if model_cache["model"] is not None:
        model_cache.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    model_record = LLMModel.query.get(model_id)
    if not model_record:
        raise ValueError(f"Model with ID {model_id} not found in the database.")

    print(f"Loading model {model_record.name} to device: {model_cache['device']}...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_record.path)
        model = AutoModelForCausalLM.from_pretrained(
            model_record.path,
            device_map=model_cache["device"]
        )

        model_cache["model_id"] = model_id
        model_cache["model"] = model
        model_cache["tokenizer"] = tokenizer

        print(f"Model {model_record.name} loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load model {model_record.name}: {e}") from e

def generate_text(model_id: int, prompt: str, max_new_tokens: int = 150):
    """Generates text using a specified model."""
    load_model(model_id)

    if model_cache["model_id"] != model_id or model_cache["model"] is None:
        raise RuntimeError(f"Model {model_id} could not be loaded for inference.")

    model = model_cache["model"]
    tokenizer = model_cache["tokenizer"]
    device = model_cache["device"]

    print(f"Generating text with model {model_id} on device {device}...")

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response_text
    except Exception as e:
        raise RuntimeError(f"Failed to generate text with model {model_id}: {e}") from e
