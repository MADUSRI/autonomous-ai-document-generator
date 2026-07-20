# Autonomous AI Agent for Business Document Generation

This project implements a simple FastAPI service that accepts a natural language request, creates a task plan, executes the planning steps, and generates a polished Microsoft Word document (.docx) as output.

## Features
- POST /agent accepts JSON: {"request": "..."}
- Autonomous multi-step planning
- Deterministic document generation with Python-docx
- Optional local LLM fallback when Ollama is running on localhost:11434
- Validation and clear API responses

## Run locally
1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Start the API:
   - `uvicorn app.main:app --reload`
3. Send a test request:
   - `curl -X POST http://127.0.0.1:8000/agent -H "Content-Type: application/json" -d '{"request":"Create a concise project proposal for a new AI scheduling assistant for small clinics."}'`

## Engineering improvement implemented
- Multi-step planning: the agent breaks the request into a structured execution plan before generating the document. This improves autonomy and makes the workflow more robust for ambiguous or complex requests.

## Verification
The project has been verified with:
- `pytest -q`
