import unittest

from pydantic import ValidationError

from app.schemas.column_mapping import ColumnMappingRequest

from app.services.column_mapping_service import (
    create_column_mapping,
)


class TestColumnMapping(unittest.TestCase):

    def setUp(self):

        self.schema_metadata = {
            "database_name": "SalesDB",
            "database_type": "sqlite",
            "tables": [
                {
                    "name": "Invoice",
                    "table_type": "table",
                    "columns": [
                        {
                            "name": "InvoiceID",
                            "data_type": "INTEGER",
                        },
                        {
                            "name": "InvoiceNo",
                            "data_type": "VARCHAR",
                        },
                        {
                            "name": "CustomerID",
                            "data_type": "INTEGER",
                        },
                        {
                            "name": "InvoiceDate",
                            "data_type": "DATE",
                        },
                        {
                            "name": "TotalAmount",
                            "data_type": "DECIMAL",
                        },
                    ],
                }
            ],
        }

    # ========================================================
    # SUCCESSFUL COLUMN MAPPING
    # ========================================================

    def test_create_column_mapping_success(self):

        request = ColumnMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            column_name="InvoiceNo",
            business_name="Invoice Number",
            description=(
                "Unique invoice number shown to customer."
            ),
        )

        result = create_column_mapping(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["database_name"],
            "SalesDB",
        )

        self.assertEqual(
            result["table_name"],
            "Invoice",
        )

        self.assertEqual(
            result["column_name"],
            "InvoiceNo",
        )

        self.assertEqual(
            result["business_name"],
            "Invoice Number",
        )

        self.assertEqual(
            result["description"],
            "Unique invoice number shown to customer.",
        )

    # ========================================================
    # SECOND EXAMPLE
    # ========================================================

    def test_amount_column_mapping_success(self):

        request = ColumnMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            column_name="TotalAmount",
            business_name="Invoice Amount",
            description="Final amount after taxes.",
        )

        result = create_column_mapping(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["column_name"],
            "TotalAmount",
        )

        self.assertEqual(
            result["business_name"],
            "Invoice Amount",
        )

        self.assertEqual(
            result["description"],
            "Final amount after taxes.",
        )

    # ========================================================
    # INVALID DATABASE
    # ========================================================

    def test_database_mismatch_is_rejected(self):

        request = ColumnMappingRequest(
            database_name="OtherDB",
            table_name="Invoice",
            column_name="InvoiceNo",
            business_name="Invoice Number",
            description="Invoice number.",
        )

        with self.assertRaises(ValueError):

            create_column_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID TABLE
    # ========================================================

    def test_invalid_table_is_rejected(self):

        request = ColumnMappingRequest(
            database_name="SalesDB",
            table_name="UnknownTable",
            column_name="InvoiceNo",
            business_name="Invoice Number",
            description="Invoice number.",
        )

        with self.assertRaises(ValueError):

            create_column_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID COLUMN
    # ========================================================

    def test_invalid_column_is_rejected(self):

        request = ColumnMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            column_name="UnknownColumn",
            business_name="Unknown",
            description="Unknown column.",
        )

        with self.assertRaises(ValueError):

            create_column_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # BUSINESS NAME REQUIRED
    # ========================================================

    def test_business_name_is_required(self):

        with self.assertRaises(ValidationError):

            ColumnMappingRequest(
                database_name="SalesDB",
                table_name="Invoice",
                column_name="InvoiceNo",
                business_name="",
                description="Invoice number.",
            )

    # ========================================================
    # DESCRIPTION REQUIRED
    # ========================================================

    def test_description_is_required(self):

        with self.assertRaises(ValidationError):

            ColumnMappingRequest(
                database_name="SalesDB",
                table_name="Invoice",
                column_name="InvoiceNo",
                business_name="Invoice Number",
                description="",
            )

    # ========================================================
    # COLUMN NAME REQUIRED
    # ========================================================

    def test_column_name_is_required(self):

        with self.assertRaises(ValidationError):

            ColumnMappingRequest(
                database_name="SalesDB",
                table_name="Invoice",
                column_name="",
                business_name="Invoice Number",
                description="Invoice number.",
            )

    # ========================================================
    # WHITESPACE CLEANING
    # ========================================================

    def test_business_name_and_description_are_trimmed(self):

        request = ColumnMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            column_name="InvoiceNo",
            business_name="  Invoice Number  ",
            description="  Unique invoice number.  ",
        )

        result = create_column_mapping(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["business_name"],
            "Invoice Number",
        )

        self.assertEqual(
            result["description"],
            "Unique invoice number.",
        )


if __name__ == "__main__":
    unittest.main()