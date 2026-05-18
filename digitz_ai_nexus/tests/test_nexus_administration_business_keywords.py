import frappe
from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.api.nexus_administration import (
    get_business_keyword_controls,
    save_business_keyword,
    set_business_keyword_enabled,
)


TEST_CATEGORY_NAME = "Synthetic Administration Keyword Category"
TEST_CATEGORY_CODE = "SYN-ADMIN-KW"
TEST_KEYWORD = "synthetic escalation"
TEST_KEYWORD_UPDATED = "synthetic escalation updated"


class TestNexusAdministrationBusinessKeywords(FrappeTestCase):
    def setUp(self):
        cleanup_test_records()
        self.category = create_test_keyword_category()

    def tearDown(self):
        cleanup_test_records()

    def test_get_business_keyword_controls_returns_categories_and_keywords(self):
        save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "High",
                "boost_weight": 2.5,
                "enabled": 1,
                "synonyms": "synthetic routing, synthetic handover",
                "description": "Synthetic keyword for administration test.",
            }
        )

        result = get_business_keyword_controls()

        self.assertIn("categories", result)
        self.assertIn("keywords", result)

        categories = result.get("categories") or []
        keywords = result.get("keywords") or []

        category_names = {row.get("name") for row in categories}
        keyword_values = {row.get("keyword") for row in keywords}

        self.assertIn(self.category, category_names)
        self.assertIn(TEST_KEYWORD, keyword_values)

    def test_save_business_keyword_creates_keyword(self):
        result = save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "High",
                "boost_weight": 3.0,
                "enabled": 1,
                "synonyms": "synthetic support, synthetic agent",
                "description": "Created from unit test.",
            }
        )

        self.assertTrue(result.get("name"))

        doc = frappe.get_doc("Nexus Business Keyword", result.get("name"))

        self.assertEqual(doc.keyword, TEST_KEYWORD)
        self.assertEqual(doc.category, self.category)
        self.assertEqual(doc.priority_level, "High")
        self.assertEqual(float(doc.boost_weight), 3.0)
        self.assertEqual(int(doc.enabled), 1)
        self.assertEqual(doc.synonyms, "synthetic support, synthetic agent")
        self.assertEqual(doc.description, "Created from unit test.")

    def test_save_business_keyword_updates_existing_keyword_by_name(self):
        created = save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "Medium",
                "boost_weight": 1.0,
                "enabled": 1,
                "synonyms": "initial synonym",
                "description": "Initial description.",
            }
        )

        updated = save_business_keyword(
            {
                "name": created.get("name"),
                "keyword": TEST_KEYWORD_UPDATED,
                "category": self.category,
                "priority_level": "Low",
                "boost_weight": 0.75,
                "enabled": 0,
                "synonyms": "updated synonym",
                "description": "Updated description.",
            }
        )

        self.assertEqual(created.get("name"), updated.get("name"))

        doc = frappe.get_doc("Nexus Business Keyword", created.get("name"))

        self.assertEqual(doc.keyword, TEST_KEYWORD_UPDATED)
        self.assertEqual(doc.category, self.category)
        self.assertEqual(doc.priority_level, "Low")
        self.assertEqual(float(doc.boost_weight), 0.75)
        self.assertEqual(int(doc.enabled), 0)
        self.assertEqual(doc.synonyms, "updated synonym")
        self.assertEqual(doc.description, "Updated description.")

    def test_duplicate_keyword_and_category_updates_existing_record(self):
        first = save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "Medium",
                "boost_weight": 1.0,
                "enabled": 1,
                "synonyms": "first synonym",
                "description": "First save.",
            }
        )

        second = save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "High",
                "boost_weight": 4.0,
                "enabled": 1,
                "synonyms": "second synonym",
                "description": "Second save should update same record.",
            }
        )

        self.assertEqual(first.get("name"), second.get("name"))

        records = frappe.get_all(
            "Nexus Business Keyword",
            filters={
                "keyword": TEST_KEYWORD,
                "category": self.category,
            },
            pluck="name",
            limit_page_length=20,
        )

        self.assertEqual(len(records), 1)

        doc = frappe.get_doc("Nexus Business Keyword", first.get("name"))

        self.assertEqual(doc.priority_level, "High")
        self.assertEqual(float(doc.boost_weight), 4.0)
        self.assertEqual(doc.synonyms, "second synonym")
        self.assertEqual(doc.description, "Second save should update same record.")

    def test_set_business_keyword_enabled_disables_keyword(self):
        created = save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "Medium",
                "boost_weight": 1.0,
                "enabled": 1,
            }
        )

        result = set_business_keyword_enabled(created.get("name"), 0)

        self.assertEqual(result.get("name"), created.get("name"))
        self.assertEqual(int(result.get("enabled")), 0)

        enabled = frappe.db.get_value(
            "Nexus Business Keyword",
            created.get("name"),
            "enabled",
        )

        self.assertEqual(int(enabled or 0), 0)

    def test_set_business_keyword_enabled_enables_keyword(self):
        created = save_business_keyword(
            {
                "keyword": TEST_KEYWORD,
                "category": self.category,
                "priority_level": "Medium",
                "boost_weight": 1.0,
                "enabled": 0,
            }
        )

        result = set_business_keyword_enabled(created.get("name"), 1)

        self.assertEqual(result.get("name"), created.get("name"))
        self.assertEqual(int(result.get("enabled")), 1)

        enabled = frappe.db.get_value(
            "Nexus Business Keyword",
            created.get("name"),
            "enabled",
        )

        self.assertEqual(int(enabled or 0), 1)

    def test_save_business_keyword_requires_keyword(self):
        with self.assertRaises(Exception):
            save_business_keyword(
                {
                    "keyword": "",
                    "category": self.category,
                    "priority_level": "Medium",
                    "boost_weight": 1.0,
                    "enabled": 1,
                }
            )

    def test_set_business_keyword_enabled_requires_existing_keyword(self):
        with self.assertRaises(Exception):
            set_business_keyword_enabled("NON-EXISTING-BUSINESS-KEYWORD", 1)


def create_test_keyword_category():
    if frappe.db.exists("Nexus Keyword Category", {"category_code": TEST_CATEGORY_CODE}):
        return frappe.db.get_value(
            "Nexus Keyword Category",
            {"category_code": TEST_CATEGORY_CODE},
            "name",
        )

    doc = frappe.new_doc("Nexus Keyword Category")
    doc.category_name = TEST_CATEGORY_NAME
    doc.category_code = TEST_CATEGORY_CODE
    doc.weight = 1.5
    doc.priority_level = "High"
    doc.enabled = 1
    doc.description = "Synthetic category for Nexus Administration business keyword tests."
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return doc.name


def cleanup_test_records():
    if frappe.db.exists("DocType", "Nexus Business Keyword"):
        keyword_names = frappe.get_all(
            "Nexus Business Keyword",
            filters=[
                ["keyword", "in", [TEST_KEYWORD, TEST_KEYWORD_UPDATED]],
            ],
            pluck="name",
            limit_page_length=100,
        )

        keyword_names += frappe.get_all(
            "Nexus Business Keyword",
            filters=[
                ["category", "=", get_test_category_name_if_exists()],
            ],
            pluck="name",
            limit_page_length=100,
        ) if get_test_category_name_if_exists() else []

        for name in set(keyword_names):
            if frappe.db.exists("Nexus Business Keyword", name):
                frappe.delete_doc(
                    "Nexus Business Keyword",
                    name,
                    force=1,
                    ignore_permissions=True,
                )

    category_name = get_test_category_name_if_exists()

    if category_name and frappe.db.exists("Nexus Keyword Category", category_name):
        frappe.delete_doc(
            "Nexus Keyword Category",
            category_name,
            force=1,
            ignore_permissions=True,
        )

    frappe.db.commit()


def get_test_category_name_if_exists():
    if not frappe.db.exists("DocType", "Nexus Keyword Category"):
        return None

    return frappe.db.get_value(
        "Nexus Keyword Category",
        {"category_code": TEST_CATEGORY_CODE},
        "name",
    )