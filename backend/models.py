from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database extension
db = SQLAlchemy()

# --- Database Models ---

class LLMModel(db.Model):
    """Represents a downloaded Large Language Model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    huggingface_id = db.Column(db.String(200), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    path = db.Column(db.String(300), nullable=True)
    def __repr__(self): return f'<LLMModel {self.name}>'

class Dataset(db.Model):
    """Represents an uploaded dataset for training."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    path = db.Column(db.String(300), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    def __repr__(self): return f'<Dataset {self.filename}>'

class TrainingJob(db.Model):
    """Represents a fine-tuning job for an LLM."""
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('llm_model.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    settings = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    logs = db.Column(db.Text, nullable=True)
    metrics = db.Column(db.JSON, nullable=True)
    model = db.relationship('LLMModel', backref=db.backref('training_jobs', lazy=True, cascade="all, delete-orphan"))
    dataset = db.relationship('Dataset', backref=db.backref('training_jobs', lazy=True, cascade="all, delete-orphan"))
    def __repr__(self): return f'<TrainingJob {self.id}>'

class CapturedError(db.Model):
    """Represents a runtime error captured by the application."""
    id = db.Column(db.Integer, primary_key=True)
    traceback = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    line_number = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='new')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    analysis = db.Column(db.Text, nullable=True)
    proposed_fix = db.Column(db.Text, nullable=True)
    def __repr__(self): return f'<CapturedError {self.id}>'

class Conversation(db.Model):
    """Represents a single chat conversation."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('llm_model.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    model = db.relationship('LLMModel', backref=db.backref('conversations', lazy=True))
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade="all, delete-orphan")
    def __repr__(self): return f'<Conversation {self.id}: {self.title}>'

class ChatMessage(db.Model):
    """Represents a single message within a conversation."""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    def __repr__(self): return f'<ChatMessage {self.id} from {self.role}>'
