def format_answer_response(raw_response):
    """
    Converts raw answer service output into UI-ready response.
    """

    raw_response = raw_response or {}

    confidence = raw_response.get("confidence") or 0
    access_status = raw_response.get("access_status")
    fallback_used = int(raw_response.get("fallback_used") or 0)

    citations = raw_response.get("citations") or []
    sources = raw_response.get("sources") or []

    return {
        "status": raw_response.get("status"),
        "access_status": access_status,
        "answer": raw_response.get("answer"),
        "display_answer": build_display_answer(raw_response),
        "confidence": confidence,
        "confidence_label": get_confidence_label(confidence),
        "grounded": bool(sources) and not fallback_used,
        "fallback_used": fallback_used,
        "citations": citations,
        "source_summary": build_source_summary(citations),
        "source_count": len(citations),
        "can_show_sources": bool(citations),
        "retrieval_debug": raw_response.get("retrieval_debug"),
        "log": raw_response.get("log"),
    }


def build_display_answer(raw_response):
    answer = (raw_response.get("answer") or "").strip()
    citations = raw_response.get("citations") or []

    if not answer:
        return ""

    if not citations:
        return answer

    source_lines = ["", "Sources:"]

    for citation in citations:
        source_no = citation.get("source_no")
        context_path = citation.get("context_path") or "Unknown Source"

        source_lines.append(f"[{source_no}] {context_path}")

    return answer + "\n".join([""] + source_lines)


def build_source_summary(citations):
    summary = []

    for citation in citations or []:
        source_no = citation.get("source_no")
        context_path = citation.get("context_path") or "Unknown Source"
        project = citation.get("project")

        label = f"[{source_no}] {context_path}"

        if project:
            label = f"{label} — {project}"

        summary.append(label)

    return summary


def get_confidence_label(confidence):
    try:
        confidence = float(confidence or 0)
    except Exception:
        confidence = 0

    if confidence >= 0.75:
        return "High"

    if confidence >= 0.40:
        return "Medium"

    if confidence > 0:
        return "Low"

    return "None"