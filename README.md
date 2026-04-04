# Mini Agent Orchestrator

This repository contains an event-driven agentic workflow designed to parse natural language requests, plan a sequence of actionable steps, and orchestrate the execution of mock asynchronous tools.

## Architecture & Design Choices

The core intent of this project is to build the orchestration logic from scratch without relying on heavy abstractions like LangChain. This ensures complete control over state management, tool execution, and failure handling.

* **Framework:** Built with **FastAPI**. It provides native support for asynchronous Python (`async`/`await`), and asynchronous tool execution (simulated via `asyncio.sleep`).

* **LLM Integration:** Utilizes the `google-genai` SDK (Gemini 2.5 Flash instead of OpenAI models, since I had a Gemini Pro Subscription).

* **Handling State & Async Tasks:** The orchestrator iterates synchronously over the async tasks derived from the LLM's plan. State is maintained locally within the endpoint via an `executed_steps` array, which acts as an append-only ledger of successful tool calls.

* **Guardrails & LLM Unreliability:** * The `cancel_order` tool simulates a 20% failure rate. 
    * The orchestrator strictly evaluates the return state of every tool. If a tool fails, the loop halts immediately.
    * By halting the loop, the system prevents downstream actions (like sending a confirmation email for an order that failed to cancel). The endpoint returns a clean HTTP 200 response containing a specific `failure` status, the generated plan, and the ledger of steps executed prior to the failure.

## Tech Stack

* **Language:** Python 3.10+
* **Web Framework:** FastAPI & Uvicorn
* **LLM Provider:** Google Gemini API (`google-genai`)
* **Validation:** Pydantic

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/sudo-boo/mini-agent-orchestrator.git](https://github.com/sudo-boo/mini-agent-orchestrator.git)
    cd mini-agent-orchestrator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your Google Gemini API key:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

> The API will be available at `http://127.0.0.1:8000`.

**API Usage Endpoint**: POST /process

**Payload:**
```JSON
{
  "request": "Cancel my order #9921 and email me the confirmation at user@example.com."
}
```

cURL Example:
```bash
curl -X POST "[http://127.0.0.1:8000/process](http://127.0.0.1:8000/process)" \
     -H "Content-Type: application/json" \
     -d '{"request": "Cancel my order #9921 and email me the confirmation at user@example.com."}'
```

## Running the Test Script
A comprehensive test suite is included to validate the golden path, edge cases, and failure states. Ensure the server is running, then execute the test script in a separate terminal:

```bash
python test-main.py
```