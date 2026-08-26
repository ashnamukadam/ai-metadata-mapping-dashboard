import unittest

from pydantic import ValidationError

from app.schemas.relationship import RelationshipRequest

from app.services.relationship_service import (
    create_relationship,
)


class TestRelationshipService(unittest.TestCase):

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
                            "primary_key": True,
                        },
                        {
                            "name": "CustomerID",
                            "data_type": "INTEGER",
                        },
                    ],
                },
                {
                    "name": "Customer",
                    "table_type": "table",
                    "columns": [
                        {
                            "name": "CustomerID",
                            "data_type": "INTEGER",
                            "primary_key": True,
                        },
                    ],
                },
                {
                    "name": "InvoiceItems",
                    "table_type": "table",
                    "columns": [
                        {
                            "name": "InvoiceItemID",
                            "data_type": "INTEGER",
                            "primary_key": True,
                        },
                        {
                            "name": "InvoiceID",
                            "data_type": "INTEGER",
                        },
                        {
                            "name": "ProductID",
                            "data_type": "INTEGER",
                        },
                    ],
                },
                {
                    "name": "Product",
                    "table_type": "table",
                    "columns": [
                        {
                            "name": "ProductID",
                            "data_type": "INTEGER",
                            "primary_key": True,
                        },
                    ],
                },
            ],
        }

    # ========================================================
    # INVOICE → CUSTOMER
    # ========================================================

    def test_invoice_customer_relationship(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="Invoice",
            parent_column="CustomerID",
            child_table="Customer",
            child_column="CustomerID",
        )

        result = create_relationship(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["parent_table"],
            "Invoice",
        )

        self.assertEqual(
            result["parent_column"],
            "CustomerID",
        )

        self.assertEqual(
            result["child_table"],
            "Customer",
        )

        self.assertEqual(
            result["child_column"],
            "CustomerID",
        )

    # ========================================================
    # INVOICE → INVOICE ITEMS
    # ========================================================

    def test_invoice_items_relationship(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="Invoice",
            parent_column="InvoiceID",
            child_table="InvoiceItems",
            child_column="InvoiceID",
        )

        result = create_relationship(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["parent_table"],
            "Invoice",
        )

        self.assertEqual(
            result["parent_column"],
            "InvoiceID",
        )

        self.assertEqual(
            result["child_table"],
            "InvoiceItems",
        )

        self.assertEqual(
            result["child_column"],
            "InvoiceID",
        )

    # ========================================================
    # PRODUCT → INVOICE ITEMS
    # ========================================================

    def test_product_relationship(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="Product",
            parent_column="ProductID",
            child_table="InvoiceItems",
            child_column="ProductID",
        )

        result = create_relationship(
            request,
            self.schema_metadata,
        )

        self.assertEqual(
            result["parent_table"],
            "Product",
        )

        self.assertEqual(
            result["parent_column"],
            "ProductID",
        )

        self.assertEqual(
            result["child_table"],
            "InvoiceItems",
        )

        self.assertEqual(
            result["child_column"],
            "ProductID",
        )

    # ========================================================
    # DATABASE MISMATCH
    # ========================================================

    def test_database_mismatch_is_rejected(self):

        request = RelationshipRequest(
            database_name="OtherDB",
            parent_table="Invoice",
            parent_column="CustomerID",
            child_table="Customer",
            child_column="CustomerID",
        )

        with self.assertRaises(ValueError):

            create_relationship(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID PARENT TABLE
    # ========================================================

    def test_invalid_parent_table_is_rejected(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="UnknownTable",
            parent_column="CustomerID",
            child_table="Customer",
            child_column="CustomerID",
        )

        with self.assertRaises(ValueError):

            create_relationship(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID CHILD TABLE
    # ========================================================

    def test_invalid_child_table_is_rejected(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="Invoice",
            parent_column="CustomerID",
            child_table="UnknownTable",
            child_column="CustomerID",
        )

        with self.assertRaises(ValueError):

            create_relationship(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID PARENT COLUMN
    # ========================================================

    def test_invalid_parent_column_is_rejected(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="Invoice",
            parent_column="UnknownColumn",
            child_table="Customer",
            child_column="CustomerID",
        )

        with self.assertRaises(ValueError):

            create_relationship(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # INVALID CHILD COLUMN
    # ========================================================

    def test_invalid_child_column_is_rejected(self):

        request = RelationshipRequest(
            database_name="SalesDB",
            parent_table="Invoice",
            parent_column="CustomerID",
            child_table="Customer",
            child_column="UnknownColumn",
        )

        with self.assertRaises(ValueError):

            create_relationship(
                request,
                self.schema_metadata,
            )

    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    def test_required_fields_are_validated(self):

        with self.assertRaises(ValidationError):

            RelationshipRequest(
                database_name="SalesDB",
                parent_table="Invoice",
                parent_column="",
                child_table="Customer",
                child_column="CustomerID",
            )

    # ========================================================
    # DATABASE NAME REQUIRED
    # ========================================================

    def test_database_name_is_required(self):

        with self.assertRaises(ValidationError):

            RelationshipRequest(
                database_name="",
                parent_table="Invoice",
                parent_column="CustomerID",
                child_table="Customer",
                child_column="CustomerID",
            )


if __name__ == "__main__":
    unittest.main()