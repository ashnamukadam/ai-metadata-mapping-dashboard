import unittest

from pydantic import ValidationError

from app.schemas.business_mapping import (
    BusinessMappingRequest,
)

from app.services.business_mapping_service import (
    create_business_mapping,
)


class TestBusinessMapping(unittest.TestCase):

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
                        {
                            "name": "Status",
                            "data_type": "VARCHAR",
                        },
                    ],
                }
            ],
        }

    # ========================================================
    # SUCCESSFUL BUSINESS MAPPING
    # ========================================================

    def test_create_business_mapping_success(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose=(
                "Invoice table stores all customer invoices."
            ),
            ai_aliases=[
                "Invoice",
                "Bill",
                "Sales Invoice",
                "Customer Bill",
            ],
            primary_identifier="InvoiceID",
            date_field="InvoiceDate",
            amount_field="TotalAmount",
            status_field="Status",
            customer_reference="CustomerID",
            description=(
                "Contains finalized customer invoices only."
            ),
        )

        result = create_business_mapping(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["database_name"],
            "SalesDB",
        )

        self.assertEqual(
            result["business_entity"],
            "Invoice",
        )

        self.assertEqual(
            result["table"],
            "Invoice",
        )

        self.assertEqual(
            result["primary_identifier"],
            "InvoiceID",
        )

        self.assertEqual(
            result["date_field"],
            "InvoiceDate",
        )

        self.assertEqual(
            result["amount_field"],
            "TotalAmount",
        )

        self.assertEqual(
            result["status_field"],
            "Status",
        )

        self.assertEqual(
            result["customer_reference"],
            "CustomerID",
        )

        self.assertEqual(
            len(result["aliases"]),
            4,
        )

    # ========================================================
    # INVALID TABLE
    # ========================================================

    def test_invalid_table_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="UnknownTable",
            business_entity="Invoice",
            table_purpose="Invoice information.",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID PRIMARY IDENTIFIER
    # ========================================================

    def test_invalid_primary_identifier_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
            primary_identifier="WrongID",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID DATE FIELD
    # ========================================================

    def test_invalid_date_field_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
            date_field="WrongDate",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID AMOUNT FIELD
    # ========================================================

    def test_invalid_amount_field_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
            amount_field="WrongAmount",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID STATUS FIELD
    # ========================================================

    def test_invalid_status_field_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
            status_field="WrongStatus",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID CUSTOMER REFERENCE
    # ========================================================

    def test_invalid_customer_reference_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
            customer_reference="WrongCustomerID",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # DATABASE MISMATCH
    # ========================================================

    def test_database_mismatch_is_rejected(self):

        request = BusinessMappingRequest(
            database_name="OtherDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
        )

        with self.assertRaises(ValueError):

            create_business_mapping(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # ALIAS CLEANING
    # ========================================================

    def test_aliases_are_cleaned(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
            ai_aliases=[
                " Invoice ",
                "Bill",
                "",
                "   ",
                "Sales Invoice",
            ],
        )

        result = create_business_mapping(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["aliases"],
            [
                "Invoice",
                "Bill",
                "Sales Invoice",
            ],
        )

    # ========================================================
    # OPTIONAL FIELDS
    # ========================================================

    def test_optional_fields_can_be_omitted(self):

        request = BusinessMappingRequest(
            database_name="SalesDB",
            table_name="Invoice",
            business_entity="Invoice",
            table_purpose="Invoice information.",
        )

        result = create_business_mapping(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["business_entity"],
            "Invoice",
        )

        self.assertIsNone(
            result["primary_identifier"],
        )

        self.assertIsNone(
            result["date_field"],
        )

        self.assertIsNone(
            result["amount_field"],
        )

        self.assertIsNone(
            result["status_field"],
        )

        self.assertIsNone(
            result["customer_reference"],
        )

    # ========================================================
    # REQUIRED BUSINESS ENTITY
    # ========================================================

    def test_business_entity_is_required(self):

        with self.assertRaises(ValidationError):

            BusinessMappingRequest(
                database_name="SalesDB",
                table_name="Invoice",
                business_entity="",
                table_purpose="Invoice information.",
            )

    # ========================================================
    # REQUIRED TABLE PURPOSE
    # ========================================================

    def test_table_purpose_is_required(self):

        with self.assertRaises(ValidationError):

            BusinessMappingRequest(
                database_name="SalesDB",
                table_name="Invoice",
                business_entity="Invoice",
                table_purpose="",
            )


if __name__ == "__main__":
    unittest.main()