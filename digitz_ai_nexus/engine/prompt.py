from digitz_ai_nexus.engine.response_mode import get_response_mode

SAFE_FALLBACK_ANSWER = "I do not have enough approved knowledge to answer this."


def build_prompt(query_contract, retrieved_chunks):
    query = query_contract.get("query")
    response_mode = get_response_mode(query_contract)

    context_blocks = []

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[Source {idx}]\n"
            f"Chunk ID: {chunk.get('chunk')}\n"
            f"Context Path: {chunk.get('context_path')}\n"
            f"Business Unit: {chunk.get('business_unit') or ''}\n"
            f"Project: {chunk.get('project') or ''}\n"
            f"Scope Type: {chunk.get('scope_type') or ''}\n"
            f"Knowledge:\n{chunk.get('chunk_text')}"
        )

    approved_knowledge = "\n\n---\n\n".join(context_blocks)

    return f"""
You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant.

CORE RULES:
1. Answer ONLY using the approved knowledge provided below.
2. Do NOT guess, invent, or add outside knowledge.
3. Do NOT expose restricted or hidden information.
4. If the approved knowledge is insufficient, answer exactly:
"{SAFE_FALLBACK_ANSWER}"
5. Keep the response aligned with the requested response behavior.

RESPONSE BEHAVIOR:
Mode: {response_mode.get("label")}
Tone: {response_mode.get("tone")}

Instructions:
{response_mode.get("instruction")}

APPROVED KNOWLEDGE:
{approved_knowledge}

USER QUESTION:
{query}

ANSWER:
""".strip()