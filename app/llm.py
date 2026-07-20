import json
import re
import time
from typing import Any, Dict, List

import httpx


def build_prompt_template(doc_type: str, request: str, subject: str) -> str:
    return (
        "You are an AI project planner. Your job is only to plan work and decompose it into tasks. "
        "Do not generate document content. Determine the most suitable document type, identify assumptions, "
        "and decompose the request into executable tasks. Return strict JSON with keys document_type, assumptions, tasks, summary. "
        "Each task must be an object with id, title, and description. "
        "Create a professional, document-type-specific task list that reflects the conventions of the target document. "
        "Prefer expert-level section headings and workstreams that are appropriate for the document type rather than generic tasks. "
        "For example, a Technical Design should include sections such as Executive Summary, Functional Requirements, Non-functional Requirements, High-Level Architecture, Component Design, Database Design, API Design, Security, Deployment, Risks, and Recommendations. "
        "A Business Proposal should include Executive Summary, Objectives, Scope, Deliverables, Timeline, Budget, Risks, and Recommendations. "
        "Meeting Minutes should include Attendees, Agenda, Discussion Summary, Decisions, Action Items, Owners, and Next Meeting. "
        "An SOP should include Purpose, Scope, Responsibilities, Procedure, Exceptions, and References. "
        "Use the document type and user request to choose the most relevant structure, and keep tasks actionable and professional. "
        f"Document type hint: {doc_type}\n"
        f"User request: {request}\n"
        f"Subject: {subject}\n"
        "Return only the JSON object."
    )


def _extract_json_payload(content: str) -> Dict[str, Any]:
    text = content.strip()
    if not text:
        return {}

    code_block_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if code_block_match:
        text = code_block_match.group(1).strip()

    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def _build_task_execution_prompt(
    request: str,
    doc_type: str,
    current_task: Dict[str, Any],
    previous_sections: List[Dict[str, Any]],
    assumptions: List[str],
) -> str:
    title = str(current_task.get("title") or current_task.get("name") or "Task").strip()
    description = str(current_task.get("description") or current_task.get("details") or "").strip()

    previous_context = ""
    if previous_sections:
        previous_context = "Previously completed sections:\n" + json.dumps(previous_sections, indent=2)

    assumptions_context = ""
    if assumptions:
        assumptions_context = "Assumptions:\n" + "\n".join(str(item).strip() for item in assumptions if str(item).strip()) + "\n"

    return (
        "You are an experienced business consultant and technical writer executing one step in a larger autonomous workflow. "
        "Your job is to generate content ONLY for the current task section of a business document. "
        "Use the original user request, the document type, all previously completed sections, and all assumptions to create detailed, professional, domain-specific content. "
        "Do not generate the entire document and do not repeat earlier sections. Avoid generic placeholders and vague language. "
        "Make reasonable assumptions when information is missing, but keep the content practical and relevant to the user's request. "
        "When appropriate, include bullet points, numbered lists, tables, implementation steps, decision criteria, or risk considerations. "
        "Return only the content for the requested section, without headings or prefatory commentary.\n"
        f"Document type: {doc_type}\n"
        f"Original request: {request}\n"
        f"Current task title: {title}\n"
        f"Current task description: {description}\n"
        f"{assumptions_context}"
        f"{previous_context}\n"
        "Generate only the content needed for this task."
    )


def execute_task(
    request: str,
    doc_type: str,
    current_task: Dict[str, Any],
    previous_sections: List[Dict[str, Any]],
    assumptions: List[str] | None = None,
) -> str:
    prompt = _build_task_execution_prompt(request, doc_type, current_task, previous_sections, assumptions or [])
    start = time.time()
    try:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:latest",
                "prompt": prompt,
                "stream": False,
            },
            timeout=600.0,
        )
        if response.status_code == 200:
            payload = response.json().get("response", "")
            if isinstance(payload, str) and payload.strip():
                return payload.strip()
        print("Time:", time.time() - start)
    except Exception as e:
        print("Time:", time.time() - start)
        import traceback
        traceback.print_exc()
        print(f"LLM Error: {e}")
        pass

    title = str(current_task.get("title") or current_task.get("name") or "Task").strip()
    description = str(current_task.get("description") or current_task.get("details") or "").strip()
    if description:
        return f"Content for {title}: {description}"
    return f"Content for {title}: the execution engine should expand this section with task-specific detail."


def try_local_llm(request: str, doc_type: str) -> Dict[str, Any]:
    start = time.time()
    try:
        from .planner import infer_subject

        subject = infer_subject(request)
        
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:latest",
                "prompt": build_prompt_template(doc_type, request, subject),
                "stream": False,
            },
            timeout=600.0,
        )
        if response.status_code == 200:
            print("Time:", time.time() - start)
            payload = _extract_json_payload(response.json().get("response", ""))
            if isinstance(payload, dict):
                assumptions = payload.get("assumptions")
                tasks = payload.get("tasks")
                if isinstance(assumptions, list):
                    normalized_assumptions = [str(item).strip() for item in assumptions if str(item).strip()]
                elif isinstance(assumptions, str) and assumptions.strip():
                    normalized_assumptions = [assumptions.strip()]
                else:
                    normalized_assumptions = []

                if isinstance(tasks, list):
                    normalized_tasks = tasks
                else:
                    normalized_tasks = []

                return {
                    "document_type": str(payload.get("document_type") or doc_type or "Business Proposal").strip(),
                    "assumptions": normalized_assumptions,
                    "tasks": normalized_tasks,
                    "summary": str(payload.get("summary") or f"Planned the work for a {doc_type.lower()}.").strip(),
                }
    except Exception as e:
        print("Time:", time.time() - start)
        import traceback
        traceback.print_exc()
        print(f"LLM Error: {e}")
    return {}
