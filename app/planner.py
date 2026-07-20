import re
from typing import Any, Dict, List

from .llm import try_local_llm


def detect_document_type(request: str) -> str:
    lowered = request.lower()
    if "technical design" in lowered or "design" in lowered:
        return "Technical Design"
    if "meeting" in lowered or "minutes" in lowered:
        return "Meeting Minutes"
    if "report" in lowered:
        return "Business Report"
    if "sop" in lowered or "standard operating" in lowered:
        return "Standard Operating Procedure"
    if "spec" in lowered or "specification" in lowered:
        return "Product Specification"
    if "plan" in lowered:
        return "Project Plan"
    return "Business Proposal"


def infer_subject(request: str) -> str:
    cleaned = request.strip()
    for prefix in ["create", "draft", "write", "generate", "prepare", "develop", "produce", "design", "build", "compose", "outline", "summarize"]:
        cleaned = re.sub(rf"^{prefix}\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(proposal|technical design|design|sop|standard operating procedure|meeting minutes|minutes|report|specification|product specification|project plan|plan|document)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,:-")
    return cleaned or request.strip()


def _normalize_tasks(tasks: Any, request: str, document_type: str) -> List[Dict[str, Any]]:
    if isinstance(tasks, list) and tasks:
        normalized: List[Dict[str, Any]] = []
        for index, task in enumerate(tasks, start=1):
            if isinstance(task, dict):
                title = str(task.get("title") or task.get("name") or f"Task {index}").strip()
                description = str(task.get("description") or task.get("details") or "").strip()
                if title:
                    normalized.append({
                        "id": task.get("id", index),
                        "title": title,
                        "description": description,
                    })
            elif isinstance(task, str) and task.strip():
                normalized.append({"id": index, "title": task.strip(), "description": ""})
        if normalized:
            return normalized

    subject = infer_subject(request).strip() or "the requested work"
    keywords = [token for token in re.findall(r"[A-Za-z0-9]+", subject.lower()) if len(token) > 3 and token not in {"that", "with", "from", "into", "about", "your", "their", "there"}]
    primary_keyword = keywords[0] if keywords else "solution"

    generated_tasks: List[Dict[str, Any]] = [
        {
            "id": 1,
            "title": f"Clarify the {document_type.lower()} objective",
            "description": f"Identify the core goal and scope for {subject}.",
        }
    ]
    if primary_keyword != "solution":
        generated_tasks.append({
            "id": 2,
            "title": f"Map the {primary_keyword} workstream",
            "description": f"Break down the main deliverables and dependencies for the {primary_keyword} portion of {subject}.",
        })
    generated_tasks.append({
        "id": len(generated_tasks) + 1,
        "title": "Capture assumptions and dependencies",
        "description": "Record constraints, risks, and open questions that may affect delivery.",
    })
    generated_tasks.append({
        "id": len(generated_tasks) + 1,
        "title": f"Prepare the {document_type.lower()} structure",
        "description": f"Organize the final document around the sections that best support {subject}.",
    })
    return generated_tasks


def _normalize_assumptions(assumptions: Any, request: str) -> List[str]:
    if isinstance(assumptions, list) and assumptions:
        normalized = [str(item).strip() for item in assumptions if str(item).strip()]
        if normalized:
            return normalized

    lowered = request.lower()
    derived: List[str] = []
    if any(token in lowered for token in ["unclear", "unknown", "missing", "uncertain", "not sure", "ambiguous"]):
        derived.append("The request contains ambiguous details, so the planner used reasonable assumptions about scope, audience, and timeline.")
    if "budget" in lowered:
        derived.append("A moderate budget was assumed for an initial implementation phase because the budget was not specified.")
    if "team" in lowered or "team size" in lowered:
        derived.append("A small cross-functional team was assumed because the team size was not specified.")
    if "timeline" in lowered or "deadline" in lowered:
        derived.append("A realistic near-term timeline was assumed because the delivery deadline was not explicitly stated.")
    if not derived:
        derived.append("The request was sufficiently clear, so the planner used a standard professional structure without additional assumptions.")
    return derived


def build_plan(request: str, doc_type: str) -> Dict[str, Any]:
    llm_result = try_local_llm(request, doc_type)
    print("hiiiiiiiiiii2222222222", llm_result)
    if llm_result:
        print("hiiiiiiiiiii2222222222")
        resolved_doc_type = str(llm_result.get("document_type") or doc_type or detect_document_type(request)).strip() or detect_document_type(request)
        return {
            "document_type": resolved_doc_type,
            "assumptions": _normalize_assumptions(llm_result.get("assumptions"), request),
            "tasks": _normalize_tasks(llm_result.get("tasks"), request, resolved_doc_type),
            "summary": str(llm_result.get("summary") or f"Planned the work for a {resolved_doc_type.lower()}.").strip(),
            "source": "llm",
        }

    fallback_doc_type = detect_document_type(request) or doc_type or "Business Proposal"
    print("hiiiiiiiiiii")
    return {
        "document_type": fallback_doc_type,
        "assumptions": _normalize_assumptions([], request),
        "tasks": _normalize_tasks([], request, fallback_doc_type),
        "summary": f"Built a fallback plan for a {fallback_doc_type.lower()}.",
        "source": "fallback",
    }
