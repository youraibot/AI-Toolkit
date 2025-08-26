import os
import subprocess
import sys
import traceback
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from .models import db, LLMModel, Dataset, TrainingJob, CapturedError, Conversation, ChatMessage

# --- Application Factory Function ---
def create_app(config_overrides=None):
    """Creates and configures an instance of the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # --- Configuration ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_uri = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(basedir, 'datasets'),
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'a-default-dev-secret-key')
    )
    if config_overrides:
        app.config.update(config_overrides)

    # --- Initialize Extensions ---
    db.init_app(app)
    Migrate(app, db)

    # --- Import Services ---
    from . import llm_service
    from . import agent_service

    # --- API Routes ---
    @app.route("/api/v1")
    def index():
        return {"message": "Flask backend is running!"}

    # LLM Model Routes
    @app.route("/api/v1/models", methods=['GET'])
    def get_models():
        models = llm_service.list_local_models()
        return jsonify([{"id": m.id, "name": m.name, "huggingface_id": m.huggingface_id, "status": m.status} for m in models])

    @app.route("/api/v1/models/search", methods=['GET'])
    def search_models_endpoint():
        query = request.args.get('q')
        if not query:
            return jsonify({"error": "Missing 'q' parameter"}), 400
        try:
            results = llm_service.search_huggingface_models(query)
            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/v1/models/download", methods=['POST'])
    def download_model_endpoint():
        data = request.get_json()
        if not data or 'model_id' not in data:
            return jsonify({"error": "Missing 'model_id'"}), 400
        try:
            model = llm_service.download_model(data['model_id'])
            return jsonify({"message": "Model downloaded", "model": {"id": model.id, "name": model.name}}), 201
        except (ValueError, IOError) as e:
            return jsonify({"error": str(e)}), 500

    # Chat & Conversation Routes
    @app.route("/api/v1/chat", methods=['POST'])
    def chat_endpoint():
        data = request.get_json()
        if not data or 'model_id' not in data or 'prompt' not in data:
            return jsonify({"error": "Missing 'model_id' or 'prompt'"}), 400
        conversation_id = data.get('conversation_id')
        prompt_text = data['prompt']
        model_id = data['model_id']
        try:
            if conversation_id:
                conversation = Conversation.query.get(conversation_id)
            else:
                title = prompt_text[:40] + '...' if len(prompt_text) > 40 else prompt_text
                conversation = Conversation(title=title, model_id=model_id)
                db.session.add(conversation)
                db.session.flush()
            user_message = ChatMessage(conversation_id=conversation.id, role='user', content=prompt_text)
            db.session.add(user_message)
            bot_response_text = llm_service.generate_text(model_id, prompt_text)
            bot_message = ChatMessage(conversation_id=conversation.id, role='bot', content=bot_response_text)
            db.session.add(bot_message)
            db.session.commit()
            return jsonify({"response": bot_response_text, "conversation_id": conversation.id})
        except (ValueError, RuntimeError) as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/v1/conversations', methods=['GET'])
    def list_conversations():
        conversations = Conversation.query.order_by(Conversation.created_at.desc()).all()
        return jsonify([{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in conversations])

    @app.route('/api/v1/conversations/<int:conv_id>', methods=['GET'])
    def get_conversation(conv_id):
        conv = Conversation.query.get_or_404(conv_id)
        messages = ChatMessage.query.filter_by(conversation_id=conv.id).order_by(ChatMessage.created_at.asc()).all()
        return jsonify({"id": conv.id, "title": conv.title, "messages": [{"role": m.role, "content": m.content} for m in messages]})

    @app.route('/api/v1/conversations/<int:conv_id>', methods=['DELETE'])
    def delete_conversation(conv_id):
        conv = Conversation.query.get_or_404(conv_id)
        db.session.delete(conv)
        db.session.commit()
        return jsonify({"message": "Conversation deleted successfully."})

    # System and Agent Routes (These might become public or be removed depending on final use case)
    @app.route('/api/v1/system/config', methods=['GET'])
    def get_system_config():
        config_data = {"upload_folder": app.config.get('UPLOAD_FOLDER'), "models_dir": llm_service.MODELS_DIR}
        return jsonify(config_data)

    @app.route('/api/v1/agent/errors', methods=['GET'])
    def list_captured_errors():
        errors = CapturedError.query.order_by(CapturedError.created_at.desc()).all()
        return jsonify([{"id": e.id, "status": e.status, "file_path": e.file_path, "line_number": e.line_number, "created_at": e.created_at.isoformat()} for e in errors])

    @app.route('/api/v1/agent/errors/<int:error_id>', methods=['GET'])
    def get_captured_error(error_id):
        error = CapturedError.query.get_or_404(error_id)
        return jsonify({"id": error.id, "status": error.status, "file_path": error.file_path, "line_number": error.line_number, "created_at": error.created_at.isoformat(), "traceback": error.traceback, "analysis": error.analysis, "proposed_fix": error.proposed_fix})

    # Global Error Handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e
        tb_str = traceback.format_exc()
        try:
            _, _, tb = sys.exc_info()
            if tb is not None:
                while tb.tb_next:
                    tb = tb.tb_next
                frame = tb.tb_frame
                lineno = tb.tb_lineno
                filename = frame.f_code.co_filename
            else:
                filename, lineno = None, None
        except Exception:
            filename, lineno = None, None
        error_record = CapturedError(traceback=tb_str, file_path=filename, line_number=lineno)
        db.session.add(error_record)
        db.session.commit()
        agent_service.analyze_error_async(error_record.id)
        return jsonify({"error": "An internal server error occurred. The issue has been logged and is being analyzed."}), 500

    return app

# --- Main Execution ---
if __name__ == "__main__":
    app = create_app()
    # Note: db.create_all() is removed. Use 'flask db upgrade'.
    app.run(host="0.0.0.0", port=5000, debug=True)
