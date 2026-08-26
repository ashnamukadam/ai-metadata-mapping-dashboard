import unittest

from pydantic import ValidationError

from app.schemas.ai_prompt_preview import (
    AIPromptPreviewRequest,
)

from app.services.ai_prompt_preview_service import (
    generate_ai_prompt_preview,
)


class TestAIPromptPreviewService(unittest.TestCase):

    # ========================================================
    # COMPLETE INVOICE PREVIEW
    # ========================================================

    def test_invoice_prompt_preview(self):

        request = AIPromptPreviewRequest(
            database_name="SalesDB",
            table_name="Invoice",
            important_fields=[
                "InvoiceNo",
                "InvoiceDate",
                "CustomerID",
                "TotalAmount",
            ],
            relationships=[
                {
                    "parent_table": "Invoice",
                    "parent_column": "CustomerID",
                    "child_table": "Customer",
                    "child_column": "CustomerID",
                },
                {
                    "parent_table": "Invoice",
                    "parent_column": "InvoiceID",
                    "child_table": "InvoiceItems",
                    "child_column": "InvoiceID",
                },
            ],
        )

        result = generate_ai_prompt_preview(request)

        self.assertIn(
            "Invoice data can be found inside table Invoice.",
            result,
        )

        self.assertIn(
            "Important fields:",
            result,
        )

        self.assertIn(
            "InvoiceNo",
            result,
        )

        self.assertIn(
            "InvoiceDate",
            result,
        )

        self.assertIn(
            "CustomerID",
            result,
        )

        self.assertIn(
            "TotalAmount",
            result,
        )

        self.assertIn(
            "Join Customer using CustomerID.",
            result,
        )

        self.assertIn(
            "Join InvoiceItems using InvoiceID.",
            result,
        )

    # ========================================================
    # EXACT PREVIEW FORMAT
    # ========================================================

    def test_exact_invoice_preview(self):

        request = AIPromptPreviewRequest(
            database_name="SalesDB",
            table_name="Invoice",
            important_fields=[
                "InvoiceNo",
                "InvoiceDate",
                "CustomerID",
                "TotalAmount",
            ],
            relationships=[
                {
                    "parent_table": "Invoice",
                    "parent_column": "CustomerID",
                    "child_table": "Customer",
                    "child_column": "CustomerID",
                },
                {
                    "parent_table": "Invoice",
                    "parent_column": "InvoiceID",
                    "child_table": "InvoiceItems",
                    "child_column": "InvoiceID",
                },
            ],
        )

        result = generate_ai_prompt_preview(request)

        expected = (
            "Invoice data can be found inside table Invoice.\n"
            "\n"
            "Important fields:\n"
            "InvoiceNo\n"
            "InvoiceDate\n"
            "CustomerID\n"
            "TotalAmount\n"
            "\n"
            "Join Customer using CustomerID.\n"
            "Join InvoiceItems using InvoiceID."
        )

        self.assertEqual(
            result,
            expected,
        )

    # ========================================================
    # NO RELATIONSHIPS
    # ========================================================

    def test_preview_without_relationships(self):

        request = AIPromptPreviewRequest(
            database_name="SalesDB",
            table_name="Customer",
            important_fields=[
                "CustomerID",
                "CustomerName",
            ],
            relationships=[],
        )

        result = generate_ai_prompt_preview(request)

        self.assertIn(
            "Customer data can be found inside table Customer.",
            result,
        )

        self.assertIn(
            "CustomerID",
            result,
        )

        self.assertIn(
            "CustomerName",
            result,
        )

        self.assertNotIn(
            "Join",
            result,
        )

    # ========================================================
    # WHITESPACE CLEANING
    # ========================================================

    def test_empty_and_whitespace_fields_are_ignored(self):

        request = AIPromptPreviewRequest(
            database_name="SalesDB",
            table_name="Invoice",
            important_fields=[
                "InvoiceNo",
                "",
                "   ",
                "InvoiceDate",
            ],
            relationships=[],
        )

        result = generate_ai_prompt_preview(request)

        self.assertIn(
            "InvoiceNo",
            result,
        )

        self.assertIn(
            "InvoiceDate",
            result,
        )

        self.assertNotIn(
            "\n\n\n",
            result,
        )

    # ========================================================
    # RELATED TABLE → SELECTED TABLE
    # ========================================================

    def test_reverse_relationship_direction(self):

        request = AIPromptPreviewRequest(
            database_name="SalesDB",
            table_name="Customer",
            important_fields=[
                "CustomerID",
                "CustomerName",
            ],
            relationships=[
                {
                    "parent_table": "Invoice",
                    "parent_column": "CustomerID",
                    "child_table": "Customer",
                    "child_column": "CustomerID",
                },
            ],
        )

        result = generate_ai_prompt_preview(request)

        self.assertIn(
            "Join Invoice using CustomerID.",
            result,
        )

    # ========================================================
    # INVALID REQUEST FIELDS
    # ========================================================

    def test_database_name_is_required(self):

        with self.assertRaises(ValidationError):

            AIPromptPreviewRequest(
                database_name="",
                table_name="Invoice",
            )

    def test_table_name_is_required(self):

        with self.assertRaises(ValidationError):

            AIPromptPreviewRequest(
                database_name="SalesDB",
                table_name="",
            )


if __name__ == "__main__":
    unittest.main()