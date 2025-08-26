import threading
import traceback
from .app import create_app
from .models import db, CapturedError
from . import llm_service

def analyze_error(error_id):
    """
    Analyzes a captured error using an LLM to propose a fix.
    This function runs in a background thread.
    """
    print(f"AGENT: Starting analysis for error ID: {error_id}")
    app = create_app()
    with app.app_context():
        error = CapturedError.query.get(error_id)
        if not error:
            print(f"AGENT: Error {error_id} not found in database.")
            return

        try:
            # Update status to 'analyzing'
            error.status = 'analyzing'
            db.session.commit()

            # Read the source code from the file where the error occurred
            try:
                with open(error.file_path, 'r') as f:
                    source_code = f.read()
            except Exception as e:
                source_code = f"Could not read source file: {e}"

            # Select the first available model for analysis
            # In a real app, this could be a specific "code-expert" model
            models = llm_service.list_local_models()
            if not models:
                raise RuntimeError("No local LLM models available for analysis.")

            analysis_model_id = models[0].id
            print(f"AGENT: Using model '{models[0].name}' for analysis.")

            # Construct a detailed prompt for the LLM
            prompt = f"""
            You are an expert software engineer debugging a Python Flask application.
            An error was captured. Your task is to analyze the error and provide a fix.

            **ERROR TRACEBACK:**
            ```
            {error.traceback}
            ```

            **FULL SOURCE CODE of {error.file_path}:**
            ```python
            {source_code}
            ```

            **INSTRUCTIONS:**
            1.  First, provide a brief, clear `EXPLANATION` of the root cause of the error.
            2.  Second, provide a `PROPOSED_FIX` in a git-style diff format. The diff should only contain the changes needed to fix the bug. Do not include the full file.

            Start your response with "EXPLANATION:" and then on a new line "PROPOSED_FIX:".
            """

            # Get the analysis from the LLM
            llm_response = llm_service.generate_text(analysis_model_id, prompt, max_new_tokens=1024)

            # Parse the response
            explanation = "Could not parse explanation."
            proposed_fix = "Could not parse proposed fix."

            if "PROPOSED_FIX:" in llm_response:
                parts = llm_response.split("PROPOSED_FIX:", 1)
                explanation = parts[0].replace("EXPLANATION:", "").strip()
                proposed_fix = parts[1].strip()
            elif "EXPLANATION:" in llm_response:
                explanation = llm_response.replace("EXPLANATION:", "").strip()

            # Update the error record with the analysis
            error.analysis = explanation
            error.proposed_fix = proposed_fix
            error.status = 'analyzed'
            db.session.commit()
            print(f"AGENT: Analysis complete for error ID: {error_id}")

        except Exception as e:
            print(f"AGENT: An unexpected error occurred during analysis of error {error_id}: {e}")
            error.status = 'analysis_failed'
            error.analysis = f"Failed to complete analysis.\n\n{traceback.format_exc()}"
            db.session.commit()


def analyze_error_async(error_id):
    """
    Triggers the error analysis in a new background thread.
    """
    thread = threading.Thread(target=analyze_error, args=(error_id,))
    thread.start()
