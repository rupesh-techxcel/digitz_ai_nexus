from digitz_ai_nexus.engine.response_mode import get_response_mode

SAFE_FALLBACK_ANSWER = "I do not have enough approved knowledge to answer this."

ROUTE_TO_KNOWLEDGE_TOKEN = "ROUTE_TO_KNOWLEDGE"


def build_router_prompt(query_contract, resolved_intents=None):
    """
    Combined intent router + conversational responder for chat mode.

    Output is one of:
    - A natural 1-2 sentence response       (conversational turn)
    - Exactly ROUTE_TO_KNOWLEDGE            (knowledge-seeking — send to RAG)
    - ACTION:ESCALATE                       (user wants a human agent)
    - ACTION:PREDEFINED:<handler-name>      (matched a predefined answer case)
    - ACTION:DECLINED:<handler-name>        (intent disabled for this profile)
    """
    original_query = (
        query_contract.get("original_query") or query_contract.get("query") or ""
    )
    conversation_context = query_contract.get("conversation_context") or ""
    intents = resolved_intents or query_contract.get("resolved_intents") or []

    context_block = (
        f"\nCONVERSATION SO FAR:\n{conversation_context}\n"
        if conversation_context
        else ""
    )

    active_intents = [i for i in intents if i.get("active")]
    disabled_intents = [i for i in intents if not i.get("active")]

    special_cases_block = ""
    if active_intents:
        lines = ["SPECIAL CASES (evaluate BEFORE routing rules, in priority order):"]
        for idx, intent in enumerate(active_intents, 1):
            name = intent["name"]
            action_type = intent.get("action_type", "predefined_answer")
            if action_type == "escalate":
                token = "ACTION:ESCALATE"
            else:
                token = f"ACTION:PREDEFINED:{name}"
            lines.append(
                f"\n[{idx}] {intent['intent_name']}\n"
                f"    Trigger: {intent['trigger_description']}\n"
                f"    If matched: respond with exactly: {token}"
            )
        special_cases_block = "\n".join(lines)

    declined_block = ""
    if disabled_intents:
        lines = ["UNAVAILABLE (acknowledge gracefully, do not route to knowledge):"]
        for intent in disabled_intents:
            lines.append(
                f"\n- {intent['intent_name']}\n"
                f"  Trigger: {intent['trigger_description']}\n"
                f"  If matched: respond with exactly: ACTION:DECLINED:{intent['name']}"
            )
        declined_block = "\n".join(lines)

    special_section = ""
    combined = "\n\n".join(filter(None, [special_cases_block, declined_block]))
    if combined:
        special_section = f"\n\n{combined}\n"

    return f"""You are the Nexus Conversation Router — the first contact point in this enterprise chat assistant.

PURPOSE:
Decide whether this message is a casual conversational exchange, matches a special case, or requires a knowledge lookup.
{special_section}
ROUTING RULES:
1. Check special cases first (listed above). If the message matches one, respond with the exact action token shown.
2. If the message is a greeting, introduction, acknowledgement, farewell, small talk, or social exchange → respond naturally in 1-2 sentences.
3. If the message asks about any topic, product, service, policy, process, feature, price, procedure, or subject that requires information → respond with exactly: {ROUTE_TO_KNOWLEDGE_TOKEN}
4. If uncertain → respond with exactly: {ROUTE_TO_KNOWLEDGE_TOKEN}
5. Never generate factual information in your response — your only roles are routing, social acknowledgement, or returning an action token.
{context_block}
USER MESSAGE:
{original_query}

RESPONSE:""".strip()


def build_host_fallback_prompt(query_contract):
    """
    Graceful LLM-generated response for chat mode when RAG finds no usable knowledge.
    No facts. No knowledge. Only warm, honest guidance.
    """
    original_query = (
        query_contract.get("original_query") or query_contract.get("query") or ""
    )
    conversation_context = query_contract.get("conversation_context") or ""

    context_block = (
        f"\nCONVERSATION SO FAR:\n{conversation_context}\n"
        if conversation_context
        else ""
    )

    return f"""You are the Nexus Conversation Host for an enterprise chat assistant.

PURPOSE:
The knowledge system has been searched and could not find confirmed information to answer the user's question.
Your job is to respond gracefully — acknowledge the user, explain the limitation honestly, and optionally invite a narrower follow-up.

STRICT RULES:
1. Do NOT state any facts, prices, policies, procedures, names, product details, or timelines.
2. Do NOT guess, infer, or extrapolate any information whatsoever.
3. You MAY acknowledge what the user asked.
4. You MAY explain that confirmed information is not currently available on this topic.
5. Do NOT ask a clarifying question or suggest that a narrower question might get a better answer — if this topic has no knowledge, a more specific version of the same topic will not either.
6. Do NOT offer to connect the user with a team member or raise a support request — that is handled separately.
7. Keep the response to 1-2 sentences maximum.
8. Tone: professional, warm, and genuinely helpful.
{context_block}
USER MESSAGE:
{original_query}

RESPONSE:""".strip()


def build_query_too_long_prompt(query_contract):
    """
    Friendly nudge when the user message exceeds the 500-character limit.
    """
    return """You are the Nexus Conversation Host for an enterprise chat assistant.

The user has sent a very long message that is too detailed to process in one go.
Politely ask them to shorten their question to a single focused query.
Keep your response to 1-2 sentences. Tone: friendly and helpful.

RESPONSE:""".strip()


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
        limit = response_sentence_limit or 10

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
9. Retrieval index entries, possible questions, intellectual summaries, context summaries, scores, and routing metadata are only search signals. Do NOT use them as factual answer content.
10. The only factual evidence you may use is the text inside each Source's Knowledge section.

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
