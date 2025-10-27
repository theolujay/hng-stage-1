# HNG Stage 1: String Analysis API

This is a RESTful API service that analyzes strings and stores their computed properties.

## Features

*   Analyzes strings for various properties.
*   Stores the analysis in a database.
*   Provides endpoints for creating, retrieving, filtering, and deleting strings.
*   Supports natural language filtering.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/hng-stage-1.git
    cd hng-stage-1
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To run the application, use the following command:

```bash
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

*   `POST /strings`: Create and analyze a new string.
*   `GET /strings/{string_value}`: Retrieve a specific string.
*   `GET /strings`: Retrieve all strings with filtering options.
*   `GET /strings/filter-by-natural-language`: Filter strings using natural language queries.
*   `DELETE /strings/{string_value}`: Delete a specific string.

## Dependencies

*   FastAPI
*   SQLModel
*   Uvicorn
*   Pytest
*   Httpx
