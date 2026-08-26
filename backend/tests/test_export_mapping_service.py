import json
import unittest

from app.schemas.export_mapping import (
    ExportEntity,
    ExportMappingRequest,
    ExportRelationship,
)

from app.services.export_mapping_service import (
    generate_mapping_json,
    generate_mapping_txt,
)


class TestExportMappingService(unittest.TestCase):

    def setUp(self):
        self.request = ExportMappingRequest(
            database="SalesDB",
            entities=[
                ExportEntity(
                    entity="Invoice",
                    table="Invoice",
                    description="Stores customer invoices.",
                    aliases=[
                        "Invoice",
                        "Bill",
                        "Sales Invoice",
                    ],
                    primary_key="InvoiceID",
                    fields={
                        "InvoiceNo": "Invoice Number",
                        "InvoiceDate": "Invoice Date",
                        "CustomerID": "Customer",
                        "TotalAmount": "Invoice Amount",
                    },
                    status_field="Status",
                )
            ],
            relationships=[
                ExportRelationship(
                    parent_table="Invoice",
                    parent_column="CustomerID",
                    child_table="Customer",
                    child_column="CustomerID",
                ),
                ExportRelationship(
                    parent_table="Invoice",
                    parent_column="InvoiceID",
                    child_table="InvoiceItems",
                    child_column="InvoiceID",
                ),
            ],
        )

    # ========================================================
    # JSON EXPORT
    # ========================================================

    def test_generate_mapping_json(self):

        result = generate_mapping_json(
            self.request
        )

        data = json.loads(result)

        self.assertEqual(
            data["database"],
            "SalesDB",
        )

        self.assertEqual(
            data["entities"][0]["entity"],
            "Invoice",
        )

        self.assertEqual(
            data["entities"][0]["table"],
            "Invoice",
        )

        self.assertEqual(
            data["entities"][0]["primaryKey"],
            "InvoiceID",
        )

        self.assertEqual(
            data["entities"][0]["fields"]["InvoiceNo"],
            "Invoice Number",
        )

        self.assertEqual(
            data["entities"][0]["fields"]["TotalAmount"],
            "Invoice Amount",
        )

        self.assertEqual(
            data["entities"][0]["statusField"],
            "Status",
        )

    # ========================================================
    # JSON RELATIONSHIPS
    # ========================================================

    def test_json_contains_relationships(self):

        result = generate_mapping_json(
            self.request
        )

        data = json.loads(result)

        self.assertIn(
            "relationships",
            data,
        )

        self.assertEqual(
            len(data["relationships"]),
            2,
        )

        relationship = data["relationships"][0]

        self.assertEqual(
            relationship["parentTable"],
            "Invoice",
        )

        self.assertEqual(
            relationship["parentColumn"],
            "CustomerID",
        )

        self.assertEqual(
            relationship["childTable"],
            "Customer",
        )

        self.assertEqual(
            relationship["childColumn"],
            "CustomerID",
        )

    # ========================================================
    # TEXT EXPORT
    # ========================================================

    def test_generate_mapping_txt(self):

        result = generate_mapping_txt(
            self.request
        )

        self.assertIn(
            "DATABASE",
            result,
        )

        self.assertIn(
            "SalesDB",
            result,
        )

        self.assertIn(
            "ENTITY",
            result,
        )

        self.assertIn(
            "Invoice",
            result,
        )

        self.assertIn(
            "TABLE",
            result,
        )

        self.assertIn(
            "DESCRIPTION",
            result,
        )

        self.assertIn(
            "Stores customer invoices.",
            result,
        )

    # ========================================================
    # TEXT ALIASES
    # ========================================================

    def test_txt_contains_aliases(self):

        result = generate_mapping_txt(
            self.request
        )

        self.assertIn(
            "ALIASES",
            result,
        )

        self.assertIn(
            "Invoice",
            result,
        )

        self.assertIn(
            "Bill",
            result,
        )

        self.assertIn(
            "Sales Invoice",
            result,
        )

    # ========================================================
    # TEXT PRIMARY KEY + FIELDS
    # ========================================================

    def test_txt_contains_primary_key_and_fields(self):

        result = generate_mapping_txt(
            self.request
        )

        self.assertIn(
            "PRIMARY KEY",
            result,
        )

        self.assertIn(
            "InvoiceID",
            result,
        )

        self.assertIn(
            "FIELDS",
            result,
        )

        self.assertIn(
            "InvoiceNo -> Invoice Number",
            result,
        )

        self.assertIn(
            "InvoiceDate -> Invoice Date",
            result,
        )

        self.assertIn(
            "CustomerID -> Customer",
            result,
        )

        self.assertIn(
            "TotalAmount -> Invoice Amount",
            result,
        )

    # ========================================================
    # TEXT STATUS FIELD
    # ========================================================

    def test_txt_contains_status_field(self):

        result = generate_mapping_txt(
            self.request
        )

        self.assertIn(
            "STATUS FIELD",
            result,
        )

        self.assertIn(
            "Status",
            result,
        )

    # ========================================================
    # TEXT RELATIONSHIPS
    # ========================================================

    def test_txt_contains_relationships(self):

        result = generate_mapping_txt(
            self.request
        )

        self.assertIn(
            "RELATIONSHIPS",
            result,
        )

        self.assertIn(
            "Invoice.CustomerID -> Customer.CustomerID",
            result,
        )

        self.assertIn(
            "Invoice.InvoiceID -> InvoiceItems.InvoiceID",
            result,
        )

    # ========================================================
    # EMPTY OPTIONAL DATA
    # ========================================================

    def test_empty_mapping_can_be_exported(self):

        request = ExportMappingRequest(
            database="SalesDB",
            entities=[],
            relationships=[],
        )

        json_result = generate_mapping_json(
            request
        )

        txt_result = generate_mapping_txt(
            request
        )

        data = json.loads(json_result)

        self.assertEqual(
            data["database"],
            "SalesDB",
        )

        self.assertEqual(
            data["entities"],
            [],
        )

        self.assertEqual(
            txt_result,
            "",
        )

    # ========================================================
    # CREDENTIALS MUST NEVER APPEAR
    # ========================================================

    def test_export_does_not_contain_credentials(self):

        json_result = generate_mapping_json(
            self.request
        )

        txt_result = generate_mapping_txt(
            self.request
        )

        sensitive_terms = [
            "password",
            "credential",
            "secret",
            "token",
        ]

        for term in sensitive_terms:
            self.assertNotIn(
                term,
                json_result.lower(),
            )

            self.assertNotIn(
                term,
                txt_result.lower(),
            )


if __name__ == "__main__":
    unittest.main()