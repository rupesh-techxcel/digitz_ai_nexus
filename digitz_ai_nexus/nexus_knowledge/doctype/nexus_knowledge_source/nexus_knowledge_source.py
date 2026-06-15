import frappe
from frappe.model.document import Document

class NexusKnowledgeSource(Document):
    def validate(self):
        if not self.title:
            frappe.throw("Title is required")

        if not self.source_type:
            frappe.throw("Source Type is required")

        if self.source_type in ["PDF", "DOCX", "TXT"] and not self.source_file:
            frappe.throw("Source File is required for uploaded documents")

        if self.source_type == "Manual" and not self.manual_content:
            frappe.throw("Manual Content is required for manual knowledge")

        if not self.status:
            self.status = "Draft"

        if not self.processing_status:
            self.processing_status = "Pending"

        if not self.embedding_status:
            self.embedding_status = "Pending"
        meta = frappe.get_meta("Nexus Knowledge Source")

        if meta.has_field("diagnostics_status") and not getattr(self, "diagnostics_status", None):
            self.diagnostics_status = "Pending"

        if meta.has_field("processing_version") and not getattr(self, "processing_version", None):
            self.processing_version = 0

        if meta.has_field("chunk_count") and not getattr(self, "chunk_count", None):
            self.chunk_count = 0

        if meta.has_field("active_chunk_count") and not getattr(self, "active_chunk_count", None):
            self.active_chunk_count = 0

        if meta.has_field("retrieval_ready") and getattr(self, "retrieval_ready", None) is None:
            self.retrieval_ready = 0

        self.reset_readiness_if_source_changed(meta)

    def reset_readiness_if_source_changed(self, meta):
        if self.is_new():
            return

        before = self.get_doc_before_save()

        if not before:
            return

        watched_fields = [
            "source_type",
            "source_file",
            "manual_content",
            "tenant",
            "business_unit",
            "project",
            "context",
            "sub_context",
            "entity_type",
            "entity",
            "topic",
            "access_policy",
        ]

        changed = any(
            meta.has_field(fieldname)
            and (before.get(fieldname) or "") != (self.get(fieldname) or "")
            for fieldname in watched_fields
        )

        if not changed:
            return

        if meta.has_field("status"):
            self.status = "Draft"

        if meta.has_field("processing_status"):
            self.processing_status = "Pending"

        if meta.has_field("embedding_status"):
            self.embedding_status = "Pending"

        if meta.has_field("diagnostics_status"):
            self.diagnostics_status = "Pending"

        if meta.has_field("validation_status"):
            self.validation_status = "Pending"

        if meta.has_field("ready_to_publish"):
            self.ready_to_publish = 0

        if meta.has_field("retrieval_ready"):
            self.retrieval_ready = 0

        if meta.has_field("needs_review"):
            self.needs_review = 0

        if meta.has_field("review_reason"):
            self.review_reason = "Source changed after preparation. Process and validate again."

        if meta.has_field("active_chunk_count"):
            self.active_chunk_count = 0

        self.disable_existing_chunks_after_source_change()

    def disable_existing_chunks_after_source_change(self):
        if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
            return

        chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")
        chunk_fields = {df.fieldname for df in chunk_meta.fields}

        if "knowledge_source" not in chunk_fields or "disabled" not in chunk_fields:
            return

        chunks = frappe.get_all(
            "Nexus Knowledge Chunk",
            filters={"knowledge_source": self.name},
            pluck="name",
            limit_page_length=5000,
        )

        for chunk_name in chunks:
            frappe.db.set_value("Nexus Knowledge Chunk", chunk_name, "disabled", 1, update_modified=True)


@frappe.whitelist()
def get_source_chat_reachability(source_name):
    """
    Walk the access chain for a knowledge source and report which AI Agent Profiles
    can reach it, and whether each profile is wired to a real user or channel route.

    Chain:
      Chunk.access_policy
        → Nexus Access Category Policy (child of Nexus Access Category)
          → Nexus AI Agent Profile Access Category
            → Nexus User Profile Assignment (active)   — desk users
            → Nexus Category Identity Route (enabled)  — live chat visitors
    """
    if not source_name:
        frappe.throw("Source name is required")

    chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")
    if not chunk_meta.has_field("access_policy"):
        return {"reachable": False, "reason": "no_access_policy_field", "profiles": []}

    # Step 1: distinct access_policies on active chunks
    raw_policies = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters={"knowledge_source": source_name, "disabled": 0},
        pluck="access_policy",
    )
    policies = list({p for p in raw_policies if p})

    if not policies:
        return {"reachable": False, "reason": "no_access_policies", "profiles": []}

    # Step 2: Access Categories that contain any of these policies
    try:
        cat_rows = frappe.get_all(
            "Nexus Access Category Policy",
            filters={"access_policy": ["in", policies]},
            fields=["parent", "access_policy"],
        )
    except Exception:
        return {"reachable": False, "reason": "access_category_lookup_failed", "profiles": []}

    categories = list({r["parent"] for r in cat_rows if r.get("parent")})

    if not categories:
        return {"reachable": False, "reason": "no_access_categories", "profiles": []}

    # Step 3: AI Agent Profiles that have any of these categories (and are enabled)
    try:
        profile_rows = frappe.get_all(
            "Nexus AI Agent Profile Access Category",
            filters={"access_category": ["in", categories], "enabled": 1},
            fields=["ai_agent_profile", "access_category"],
        )
    except Exception:
        return {"reachable": False, "reason": "profile_lookup_failed", "profiles": []}

    profile_names = list({r["ai_agent_profile"] for r in profile_rows if r.get("ai_agent_profile")})

    if not profile_names:
        return {"reachable": False, "reason": "no_agent_profiles", "profiles": []}

    # Step 4a: Fetch human-readable label for each profile (agent field = title_field)
    profile_labels = {}
    agent_name_counts = {}
    try:
        for row in frappe.get_all(
            "Nexus AI Agent Profile",
            filters={"name": ["in", profile_names]},
            fields=["name", "agent"],
        ):
            agent_val = row.get("agent") or ""
            profile_labels[row["name"]] = agent_val
            agent_name_counts[agent_val] = agent_name_counts.get(agent_val, 0) + 1
    except Exception:
        pass

    # Step 4: For each profile, check real-world assignments and routes
    profiles = []
    for profile_name in sorted(profile_names):
        assignments = []
        routes = []

        try:
            user_assignments = frappe.get_all(
                "Nexus User Profile Assignment",
                filters={"ai_agent_profile": profile_name, "active": 1},
                fields=["user"],
            )
            assignments = [a["user"] for a in user_assignments if a.get("user")]
        except Exception:
            pass

        try:
            identity_routes = frappe.get_all(
                "Nexus Category Identity Route",
                filters={"ai_agent_profile": profile_name, "enabled": 1},
                fields=["channel", "chat_category", "is_public_route"],
            )
            routes = [
                {
                    "channel": r.get("channel") or "",
                    "chat_category": r.get("chat_category") or "",
                    "is_public_route": r.get("is_public_route") or 0,
                }
                for r in identity_routes
            ]
        except Exception:
            pass

        agent_val = profile_labels.get(profile_name, "")
        if agent_val and agent_name_counts.get(agent_val, 1) > 1:
            label = f"{agent_val} ({profile_name[:6]})"
        else:
            label = agent_val or profile_name

        profiles.append({
            "profile": profile_name,
            "profile_label": label,
            "user_assignments": assignments,
            "identity_routes": routes,
            "reachable": bool(assignments or routes),
        })

    reachable_profiles = [p for p in profiles if p["reachable"]]

    return {
        "reachable": bool(reachable_profiles),
        "reason": "ok" if reachable_profiles else "no_assignments",
        "profiles": profiles,
        "reachable_count": len(reachable_profiles),
        "total_profile_count": len(profiles),
        "policies_found": len(policies),
        "categories_found": len(categories),
    }


@frappe.whitelist()
def get_source_quality_panel(source_name):
    if not source_name:
        frappe.throw("Source name is required")

    source = frappe.get_doc("Nexus Knowledge Source", source_name)

    chunks = []
    chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")

    chunk_fields = [
        "name",
        "knowledge_unit",
        "knowledge_source",
        "chunk_index",
        "chunk_hash",
        "embedding",
        "embedding_status",
        "creation",
        "modified"
    ]

    optional_fields = [
        "chunk_text",
        "content",
        "text",
        "source_version",
        "archived",
        "disabled",
        "character_count",
        "diagnostics_status",
        "diagnostics_message",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "context_path"
    ]

    for fieldname in optional_fields:
        if chunk_meta.has_field(fieldname):
            chunk_fields.append(fieldname)

    filters = {}

    if chunk_meta.has_field("knowledge_source"):
        filters["knowledge_source"] = source.name
    elif source.generated_knowledge_unit:
        filters["knowledge_unit"] = source.generated_knowledge_unit

    if filters:
        chunks = frappe.get_all(
            "Nexus Knowledge Chunk",
            filters=filters,
            fields=chunk_fields,
            order_by="source_version desc, chunk_index asc",
            limit_page_length=500
        )

    active_chunks = []
    archived_chunks = []

    for chunk in chunks:
        content = (
            chunk.get("chunk_text")
            or chunk.get("content")
            or chunk.get("text")
            or ""
        )

        chunk["content"] = content
        chunk["preview"] = content[:220]
        chunk["character_count"] = chunk.get("character_count") or len(content or "")
        chunk["has_embedding"] = bool(chunk.get("embedding"))

        is_archived = bool(chunk.get("archived"))
        is_disabled = bool(chunk.get("disabled"))

        chunk["is_active"] = not is_archived and not is_disabled

        if chunk["is_active"]:
            active_chunks.append(chunk)
        else:
            archived_chunks.append(chunk)

    embedded_count = 0
    missing_embedding_count = 0
    warning_count = 0
    critical_count = 0
    duplicate_count = 0
    seen_hashes = set()

    for chunk in active_chunks:
        if chunk.get("has_embedding"):
            embedded_count += 1
        else:
            missing_embedding_count += 1

        chunk_hash = chunk.get("chunk_hash")

        if chunk_hash:
            if chunk_hash in seen_hashes:
                duplicate_count += 1
                chunk["duplicate_chunk"] = 1
            else:
                seen_hashes.add(chunk_hash)
                chunk["duplicate_chunk"] = 0
        else:
            chunk["duplicate_chunk"] = 0

        diagnostics_status = chunk.get("diagnostics_status") or "Pending"
        chunk["diagnostics_status"] = diagnostics_status

        if diagnostics_status == "Critical":
            critical_count += 1
        elif diagnostics_status == "Warning":
            warning_count += 1

    for chunk in archived_chunks:
        chunk["duplicate_chunk"] = 0
        chunk["diagnostics_status"] = chunk.get("diagnostics_status") or "Archived"

    active_chunk_count = len(active_chunks)

    if active_chunk_count:
        if embedded_count == active_chunk_count:
            embedding_status = "Completed"
        elif embedded_count > 0:
            embedding_status = "Pending"
        else:
            embedding_status = "Failed"
    else:
        embedding_status = source.embedding_status or "Pending"

    if critical_count > 0 or missing_embedding_count > 0:
        diagnostics_status = "Critical"
    elif warning_count > 0 or duplicate_count > 0:
        diagnostics_status = "Warning"
    elif active_chunk_count > 0:
        diagnostics_status = "Healthy"
    else:
        diagnostics_status = source.diagnostics_status or "Pending"

    retrieval_ready = (
        source.status == "Published"
        and embedding_status == "Completed"
        and diagnostics_status == "Healthy"
        and active_chunk_count > 0
    )

    return {
        "source": source.name,
        "title": source.title,
        "processing_status": source.processing_status,
        "processing_version": getattr(source, "processing_version", 0) or 0,
        "embedding_status": embedding_status,
        "diagnostics_status": diagnostics_status,
        "retrieval_ready": 1 if retrieval_ready else 0,

        "chunk_count": len(chunks),
        "active_chunk_count": active_chunk_count,
        "archived_chunk_count": len(archived_chunks),

        "embedded_count": embedded_count,
        "missing_embedding_count": missing_embedding_count,
        "duplicate_count": duplicate_count,
        "warning_count": warning_count,
        "critical_count": critical_count,

        "last_processed_on": source.last_processed_on,
        "generated_knowledge_unit": source.generated_knowledge_unit,
        "extracted_text_preview": source.extracted_text_preview,
        "error_log": source.error_log,

        "chunks": active_chunks + archived_chunks
    }
