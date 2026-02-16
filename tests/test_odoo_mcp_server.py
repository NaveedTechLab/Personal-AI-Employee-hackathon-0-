#!/usr/bin/env python3
"""
Tests for Odoo MCP Server
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent / ".claude" / "skills" / "odoo-mcp-server" / "scripts"))

from models import (
    AccountBalance,
    ApprovalRequest,
    ApprovalStatus,
    Invoice,
    InvoiceLine,
    InvoiceState,
    MoveType,
    OdooConfig,
    Payment,
)


class TestOdooModels(unittest.TestCase):
    """Test Odoo data models"""

    def test_move_type_values(self):
        """Test MoveType enum values"""
        self.assertEqual(MoveType.OUT_INVOICE.value, "out_invoice")
        self.assertEqual(MoveType.IN_INVOICE.value, "in_invoice")
        self.assertEqual(MoveType.OUT_REFUND.value, "out_refund")

    def test_invoice_state_values(self):
        """Test InvoiceState enum values"""
        self.assertEqual(InvoiceState.DRAFT.value, "draft")
        self.assertEqual(InvoiceState.POSTED.value, "posted")

    def test_invoice_line_to_odoo_format(self):
        """Test InvoiceLine conversion to Odoo format"""
        line = InvoiceLine(
            name="Test Product",
            quantity=5,
            price_unit=100.0,
            discount=10.0
        )
        result = line.to_odoo_format()

        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 0)
        self.assertEqual(result[2]["name"], "Test Product")
        self.assertEqual(result[2]["quantity"], 5)
        self.assertEqual(result[2]["price_unit"], 100.0)

    def test_invoice_to_odoo_create_vals(self):
        """Test Invoice conversion to Odoo create values"""
        invoice = Invoice(
            partner_id=1,
            move_type=MoveType.OUT_INVOICE,
            invoice_line_ids=[
                InvoiceLine(name="Service", quantity=1, price_unit=500)
            ],
            invoice_date="2024-01-15"
        )
        vals = invoice.to_odoo_create_vals()

        self.assertEqual(vals["partner_id"], 1)
        self.assertEqual(vals["move_type"], "out_invoice")
        self.assertEqual(vals["invoice_date"], "2024-01-15")
        self.assertEqual(len(vals["invoice_line_ids"]), 1)

    def test_invoice_from_odoo_record(self):
        """Test Invoice creation from Odoo record"""
        record = {
            "id": 123,
            "name": "INV/2024/001",
            "partner_id": [1, "Test Customer"],
            "move_type": "out_invoice",
            "state": "draft",
            "amount_total": 1500.0,
            "amount_residual": 1500.0
        }
        invoice = Invoice.from_odoo_record(record)

        self.assertEqual(invoice.id, 123)
        self.assertEqual(invoice.name, "INV/2024/001")
        self.assertEqual(invoice.partner_id, 1)
        self.assertEqual(invoice.move_type, MoveType.OUT_INVOICE)
        self.assertEqual(invoice.amount_total, 1500.0)

    def test_payment_to_odoo_create_vals(self):
        """Test Payment conversion to Odoo create values"""
        payment = Payment(
            partner_id=1,
            amount=500.0,
            payment_date="2024-01-20",
            journal_id=7,
            payment_type="inbound",
            partner_type="customer"
        )
        vals = payment.to_odoo_create_vals()

        self.assertEqual(vals["partner_id"], 1)
        self.assertEqual(vals["amount"], 500.0)
        self.assertEqual(vals["date"], "2024-01-20")
        self.assertEqual(vals["journal_id"], 7)

    def test_odoo_config_defaults(self):
        """Test OdooConfig default values"""
        config = OdooConfig()

        self.assertEqual(config.url, "http://localhost:8069")
        self.assertEqual(config.database, "odoo")
        self.assertEqual(config.timeout_seconds, 30)
        self.assertEqual(config.invoice_threshold, 1000.0)
        self.assertIn("post_invoice", config.always_require_approval)

    def test_approval_request_to_dict(self):
        """Test ApprovalRequest serialization"""
        request = ApprovalRequest(
            id="approval_123",
            operation="create_invoice",
            model="account.move",
            amount=1500.0,
            status=ApprovalStatus.PENDING,
            requested_by="claude"
        )
        result = request.to_dict()

        self.assertEqual(result["id"], "approval_123")
        self.assertEqual(result["operation"], "create_invoice")
        self.assertEqual(result["amount"], 1500.0)
        self.assertEqual(result["status"], "pending")


class TestOdooApprovalWorkflow(unittest.TestCase):
    """Test Odoo approval workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_odoo.db")

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_requires_approval_for_post_invoice(self):
        """Test that post_invoice always requires approval"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("post_invoice"))

    def test_requires_approval_for_create_payment(self):
        """Test that create_payment always requires approval"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("create_payment"))

    def test_requires_approval_for_high_value_invoice(self):
        """Test that high-value invoices require approval"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        self.assertTrue(workflow.requires_approval("create_invoice", 1500.0))
        self.assertFalse(workflow.requires_approval("create_invoice", 500.0))

    def test_create_approval_request(self):
        """Test creating approval request"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_invoice",
            model="account.move",
            data={"partner_id": 1, "amount_total": 1500},
            amount=1500.0
        )

        self.assertIsNotNone(request.id)
        self.assertTrue(request.id.startswith("odoo_approval_"))
        self.assertEqual(request.operation, "create_invoice")
        self.assertEqual(request.amount, 1500.0)
        self.assertEqual(request.status, ApprovalStatus.PENDING)

    def test_get_approval_request(self):
        """Test retrieving approval request"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        created = workflow.create_approval_request(
            operation="post_invoice",
            record_id=123,
            amount=500.0
        )

        retrieved = workflow.get_request(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(created.id, retrieved.id)
        self.assertEqual(retrieved.operation, "post_invoice")

    def test_approve_request(self):
        """Test approving a request"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_payment",
            amount=1000.0
        )

        approved = workflow.approve_request(request.id, "finance_manager")

        self.assertIsNotNone(approved)
        self.assertEqual(approved.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved.approved_by, "finance_manager")
        self.assertIsNotNone(approved.approved_at)

    def test_reject_request(self):
        """Test rejecting a request"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="create_invoice",
            amount=5000.0
        )

        rejected = workflow.reject_request(
            request.id,
            "finance_manager",
            "Amount too high"
        )

        self.assertIsNotNone(rejected)
        self.assertEqual(rejected.status, ApprovalStatus.REJECTED)
        self.assertEqual(rejected.rejection_reason, "Amount too high")

    def test_get_pending_requests(self):
        """Test getting pending requests"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)

        # Create multiple requests
        workflow.create_approval_request(operation="create_invoice", amount=1500)
        workflow.create_approval_request(operation="post_invoice", amount=500)
        req3 = workflow.create_approval_request(operation="create_payment", amount=2000)

        # Approve one
        workflow.approve_request(req3.id, "admin")

        pending = workflow.get_pending_requests()
        self.assertEqual(len(pending), 2)

    def test_is_approved(self):
        """Test is_approved check"""
        from approval_workflow import OdooApprovalWorkflow

        workflow = OdooApprovalWorkflow(db_path=self.db_path)
        request = workflow.create_approval_request(
            operation="post_invoice",
            amount=1000.0
        )

        self.assertFalse(workflow.is_approved(request.id))

        workflow.approve_request(request.id, "admin")

        self.assertTrue(workflow.is_approved(request.id))


if __name__ == "__main__":
    unittest.main()
