# Agent Instructions for the AI Toolkit

This document provides guidance for AI agents working on this codebase.

## Project Structure

The project is a full-stack web application with a Python backend and a React frontend.

- **`backend/`**: Contains the Flask backend application.
  - **`app/`**: The main application module.
    - **`__init__.py`**: Application factory and configuration.
    - **`models.py`**: SQLAlchemy database models.
    - **`routes.py`**: API endpoints.
    - **`services.py`**: Business logic for interacting with LLMs, datasets, and training jobs.
  - **`migrations/`**: Alembic database migration scripts.
  - **`venv/`**: Python virtual environment.
  - **`requirements.txt`**: Python dependencies.
- **`frontend/`**: Contains the React frontend application.
  - **`src/`**: React source code.
    - **`components/`**: React components.
    - **`App.js`**: Main application component with routing.
  - **`public/`**: Static assets.
  - **`package.json`**: Frontend dependencies and scripts.
- **`install.sh`**: Installation script for deploying the application on a fresh Ubuntu server.
- **`apache.conf`**: Apache configuration template.

## Development Environment

The application is designed to be run in a containerized environment, but it can also be run locally for development.

### Backend

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv backend/venv
    ```
2.  **Activate the virtual environment:**
    ```bash
    source backend/venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  **Run the development server:**
    ```bash
    flask run
    ```

### Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm start
    ```

## Running Tests

The project has a test suite for the backend, which you can run using `pytest`.

1.  **Activate the backend virtual environment:**
    ```bash
    source backend/venv/bin/activate
    ```
2.  **Run the tests:**
    ```bash
    pytest
    ```

There are currently no automated tests for the frontend.

## Coding Conventions

- **Python:** Follow the PEP 8 style guide.
- **JavaScript:** Follow the Airbnb JavaScript Style Guide.

## Important Notes

- The application is designed to be deployed on a bare-metal Ubuntu server using the `install.sh` script.
- The application does not have any user authentication.
- The `install.sh` script is designed to be idempotent. It can be run multiple times without causing issues.
- When making changes to the database models, you will need to generate a new migration script:
  ```bash
  flask db migrate -m "A short description of the changes"
  ```
  Then, apply the migration:
  ```bash
  flask db upgrade
  ```
- Always ensure that the `install.sh` script is updated to reflect any changes to the installation process.
- Before submitting any changes, make sure that the backend tests pass and that the frontend application builds successfully.
