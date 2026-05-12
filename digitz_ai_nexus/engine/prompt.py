from digitz_ai_nexus.engine.response_mode import get_response_mode

SAFE_FALLBACK_ANSWER = "I do not have enough approved knowledge to answer this."


def build_prompt(query_contract, retrieved_chunks):
    query = query_contract.get("query")
    original_query = query_contract.get("original_query") or query
    conversation_context = query_contract.get("conversation_context")
    response_sentence_limit = query_contract.get("response_sentence_limit")
    is_follow_up = query_contract.get("is_follow_up")

    response_mode = get_response_mode(query_contract)
    response_mode_key = query_contract.get("response_mode") or query_contract.get("use_case")
    
    is_chat_mode = str(response_mode_key or "").lower() in {"chat", "live chat"}

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

    chat_context_block = ""

    if is_chat_mode and conversation_context:
        chat_context_block = f"""
CONVERSATION CONTEXT:
{conversation_context}

CONVERSATION CONTEXT RULES:
1. Use the conversation context only to understand the user's follow-up.
2. Do NOT treat conversation context as approved factual knowledge.
3. Do NOT answer from conversation context alone.
4. Final factual/business answer must still come only from APPROVED KNOWLEDGE.
""".strip()

    chat_response_rules = ""

    if is_chat_mode:
        limit = response_sentence_limit or 6

        chat_response_rules = f"""
CHAT RESPONSE RULES:
1. Keep the answer conversational and natural.
2. Do not produce a long article-style response.
3. Limit the answer to a maximum of {limit} sentences.
4. If the user asks a follow-up, answer in continuation of the conversation.
5. If approved knowledge is insufficient, answer exactly:
"{SAFE_FALLBACK_ANSWER}"
""".strip()

    qa_response_rules = ""

    if not is_chat_mode:
        qa_response_rules = """
Q&A RESPONSE RULES:
1. Treat the user request as a direct knowledge search.
2. Provide a clear and sufficiently detailed answer when approved knowledge is available.
3. Do not behave like a conversational chat memory agent.
4. Do not use conversation continuity.
""".strip()

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

{chat_context_block}

{chat_response_rules}

{qa_response_rules}

APPROVED KNOWLEDGE:
{approved_knowledge}

CURRENT USER MESSAGE:
{original_query}

RETRIEVAL QUERY USED:
{query}

FOLLOW-UP DETECTED:
{bool(is_follow_up)}

ANSWER:
""".strip()