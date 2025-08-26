# Local AI Management and Development Platform

This project is a self-hosted web application that provides a comprehensive suite of tools for managing, fine-tuning, and evaluating local Large Language Models (LLMs). It also includes a unique "Code Health" feature that uses an LLM to diagnose and suggest fixes for its own backend errors.

The application is designed to be deployed on a bare-metal Ubuntu server and run without requiring user authentication, providing a simple, single-user experience.

## Features

*   **Model Management:** Download and manage open-source LLMs from the Hugging Face Hub. Chat with the models through a simple interface.
*   **Fine-Tuning:** Fine-tune models on your own datasets. Upload a dataset in CSV format, configure training parameters, and run the fine-tuning process.
*   **Evaluation:** Evaluate fine-tuned models to assess their performance. The system calculates and stores metrics like perplexity, accuracy, and loss.
*   **Code Health:** A diagnostic tool for developers. The application catches its own backend exceptions, sends the traceback and relevant source code to a designated LLM, and displays the AI-generated analysis and suggested fix in a dashboard.

## Tech Stack

*   **Backend:** Flask (Python)
*   **Frontend:** React (JavaScript)
*   **Database:** PostgreSQL
*   **LLM Engine:** Hugging Face `transformers`
*   **Deployment:** Apache on Ubuntu

## Installation

This application is designed for deployment on a fresh Ubuntu 22.04 LTS server. The following steps will guide you through the installation process.

### 1. Prerequisites

Ensure you have an Ubuntu 22.04 server with `git` installed.

### 2. Clone the Repository

Clone this repository to your server:
```bash
git clone <repository_url>
cd <repository_name>
```

### 3. Run the Installation Script

The `install.sh` script automates the entire setup process. It will:
- Install system dependencies (Apache, PostgreSQL, Python, etc.).
- Set up a Python virtual environment.
- Configure the PostgreSQL database and user.
- Install Python and Node.js dependencies.
- Build the React frontend.
- Configure and enable an Apache virtual host for the application.

To run the script, make it executable and run it with `sudo`:
```bash
chmod +x install.sh
sudo ./install.sh
```

The script will prompt you for a database password during execution. Please enter a secure password when prompted.

### 4. Access the Application

Once the script finishes, the application will be accessible via your server's IP address or domain name in a web browser. No login is required.

## Usage

-   **Model Management:** Navigate to the "Models" page to download new models or chat with existing ones.
-   **Fine-Tuning:** Go to the "Fine-Tune" page, upload a CSV dataset, and start the training job.
-   **Evaluation:** Visit the "Evaluate" page to measure the performance of your fine-tuned models.
-   **Code Health:** If backend errors occur, they will appear on the "Code Health" page with an AI-generated analysis.
