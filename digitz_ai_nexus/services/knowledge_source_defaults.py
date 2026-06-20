DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE = "Knowledge Source"


def apply_knowledge_source_defaults(source_doc):
    """Normalize source fields shared by every creation and processing path."""
    if (
        source_doc.meta.has_field("entity_type")
        and not source_doc.get("entity_type")
    ):
        source_doc.set("entity_type", DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE)

    if source_doc.meta.has_field("entity") and not source_doc.get("entity"):
        source_doc.set(
            "entity",
            source_doc.get("title")
            or source_doc.get("source_title")
            or source_doc.name,
        )

    return source_doc
