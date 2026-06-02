from digitz_ai_nexus.engine.response_mode import get_response_mode

SAFE_FALLBACK_ANSWER = "I do not have enough approved knowledge to answer this."


def _resolve_profile_fields(query_contract):
    """
    Extract AI Agent Profile behaviour fields from query_contract.

    Priority:
    1. query_contract["ai_profile"] dict (structured, from query contract)
    2. query_contract["agent_*"] flat fields (legacy/direct pass-through)
    """
    ai_profile = query_contract.get("ai_profile") or {}

    return {
        "behavior_prompt": (
            ai_profile.get("behavior_prompt")
            or query_contract.get("agent_behavior_prompt")
        ),
        "tone": (
            ai_profile.get("tone")
            or query_contract.get("agent_tone")
        ),
        "response_style": (
            ai_profile.get("response_style")
            or query_contract.get("agent_response_style")
        ),
        "fallback_message": (
            ai_profile.get("fallback_message")
            or query_contract.get("agent_fallback_message")
        ),
        "do_not_answer_rules": (
            ai_profile.get("do_not_answer_rules")
            or query_contract.get("agent_do_not_answer_rules")
        ),
    }


def build_prompt(query_contract, retrieved_chunks):
    query = query_contract.get("query")
    original_query = query_contract.get("original_query") or query
    conversation_context = query_contract.get("conversation_context")
    response_sentence_limit = query_contract.get("response_sentence_limit")
    is_follow_up = query_contract.get("is_follow_up")

    profile = _resolve_profile_fields(query_contract)

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
3. Preserve exact named facts from the approved knowledge.
4. Do not behave like a conversational chat memory agent.
5. Do not use conversation continuity.
""".strip()

    # Use profile tone/style if configured; fall back to generic response mode values.
    final_tone = profile.get("tone") or response_mode.get("tone")
    final_mode_label = response_mode.get("label")
    final_instruction = response_mode.get("instruction")

    behavior_block = ""
    if profile.get("behavior_prompt"):
        behavior_block = f"""
AGENT BEHAVIOUR:
{profile["behavior_prompt"]}
""".strip()

    style_block = ""
    if profile.get("response_style"):
        style_block = f"Response Style: {profile['response_style']}"

    do_not_answer_block = ""
    if profile.get("do_not_answer_rules"):
        do_not_answer_block = f"""
DO NOT ANSWER RULES:
{profile["do_not_answer_rules"]}
""".strip()

    safe_fallback = profile.get("fallback_message") or SAFE_FALLBACK_ANSWER

    return f"""
You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant.

CORE RULES:
1. Answer ONLY using the approved knowledge provided below.
2. Do NOT guess, invent, or add outside knowledge.
3. Do NOT expose restricted or hidden information.
4. If approved knowledge contains an exact named rule, label, policy, code, protocol, index, project override, or identifier, preserve that exact phrase in the answer.
5. Do NOT replace named labels with generic paraphrases.
6. If the source contains a project-specific rule name, include that rule name exactly as written.
7. If the approved knowledge is insufficient, answer exactly:
"{safe_fallback}"
8. Keep the response aligned with the requested response behavior.

RESPONSE BEHAVIOR:
Mode: {final_mode_label}
Tone: {final_tone}
{style_block}

Instructions:
{final_instruction}

{behavior_block}

{do_not_answer_block}

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