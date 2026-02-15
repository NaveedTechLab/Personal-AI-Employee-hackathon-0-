#!/usr/bin/env python3
"""
Mock Odoo Server - Simulates Odoo 17 ERP on port 8069
Rich demo data for Personal AI Employee dashboard testing.
"""

import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import random

# ============================================================
# DEMO DATA - Partners / Customers / Vendors
# ============================================================
DEMO_PARTNERS = [
    {"id": 1, "name": "Acme Corp", "email": "contact@acme.com", "phone": "+1-555-0101", "city": "New York", "country": "USA", "type": "customer", "credit_limit": 50000, "total_invoiced": 13750.00, "is_company": True},
    {"id": 2, "name": "TechStart Inc", "email": "hello@techstart.io", "phone": "+1-555-0202", "city": "San Francisco", "country": "USA", "type": "customer", "credit_limit": 30000, "total_invoiced": 12500.00, "is_company": True},
    {"id": 3, "name": "Global Traders Ltd", "email": "info@globaltraders.com", "phone": "+44-20-7946-0958", "city": "London", "country": "UK", "type": "customer", "credit_limit": 75000, "total_invoiced": 3200.00, "is_company": True},
    {"id": 4, "name": "Naveed Qureshi", "email": "qureshinaveedgiaic@gmail.com", "phone": "+92-300-1234567", "city": "Karachi", "country": "Pakistan", "type": "customer", "credit_limit": 100000, "total_invoiced": 0, "is_company": False},
    {"id": 5, "name": "Dubai Digital LLC", "email": "sales@dubaidigital.ae", "phone": "+971-4-555-9999", "city": "Dubai", "country": "UAE", "type": "customer", "credit_limit": 60000, "total_invoiced": 45000.00, "is_company": True},
    {"id": 6, "name": "Ali Hassan Trading", "email": "ali@ahtrading.pk", "phone": "+92-21-3456789", "city": "Lahore", "country": "Pakistan", "type": "customer", "credit_limit": 25000, "total_invoiced": 8900.00, "is_company": True},
    {"id": 7, "name": "AWS Cloud Services", "email": "billing@aws.amazon.com", "phone": "+1-206-266-1000", "city": "Seattle", "country": "USA", "type": "vendor", "credit_limit": 0, "total_invoiced": 0, "is_company": True},
    {"id": 8, "name": "Google Cloud Platform", "email": "cloud-billing@google.com", "phone": "+1-650-253-0000", "city": "Mountain View", "country": "USA", "type": "vendor", "credit_limit": 0, "total_invoiced": 0, "is_company": True},
    {"id": 9, "name": "Vercel Inc", "email": "billing@vercel.com", "phone": "+1-415-000-0001", "city": "San Francisco", "country": "USA", "type": "vendor", "credit_limit": 0, "total_invoiced": 0, "is_company": True},
    {"id": 10, "name": "Fatima Enterprises", "email": "fatima@fenterprises.pk", "phone": "+92-42-7890123", "city": "Islamabad", "country": "Pakistan", "type": "customer", "credit_limit": 40000, "total_invoiced": 15600.00, "is_company": True},
    {"id": 11, "name": "Berlin Software GmbH", "email": "kontakt@berlinsw.de", "phone": "+49-30-12345678", "city": "Berlin", "country": "Germany", "type": "customer", "credit_limit": 55000, "total_invoiced": 22000.00, "is_company": True},
    {"id": 12, "name": "Tokyo Tech Solutions", "email": "info@tokyotech.jp", "phone": "+81-3-1234-5678", "city": "Tokyo", "country": "Japan", "type": "customer", "credit_limit": 80000, "total_invoiced": 31500.00, "is_company": True},
]

# ============================================================
# DEMO DATA - Invoices (account.move)
# ============================================================
DEMO_INVOICES = [
    {"id": 1001, "name": "INV/2026/0001", "partner_id": 1, "partner": "Acme Corp", "amount_total": 5000.00, "amount_due": 0, "state": "posted", "payment_state": "paid", "invoice_date": "2026-01-15", "due_date": "2026-02-15", "currency": "USD", "type": "out_invoice"},
    {"id": 1002, "name": "INV/2026/0002", "partner_id": 2, "partner": "TechStart Inc", "amount_total": 12500.00, "amount_due": 12500.00, "state": "draft", "payment_state": "not_paid", "invoice_date": "2026-02-05", "due_date": "2026-03-05", "currency": "USD", "type": "out_invoice"},
    {"id": 1003, "name": "INV/2026/0003", "partner_id": 3, "partner": "Global Traders Ltd", "amount_total": 3200.00, "amount_due": 3200.00, "state": "posted", "payment_state": "not_paid", "invoice_date": "2026-02-10", "due_date": "2026-03-10", "currency": "GBP", "type": "out_invoice"},
    {"id": 1004, "name": "INV/2026/0004", "partner_id": 1, "partner": "Acme Corp", "amount_total": 8750.00, "amount_due": 0, "state": "posted", "payment_state": "paid", "invoice_date": "2026-02-12", "due_date": "2026-03-12", "currency": "USD", "type": "out_invoice"},
    {"id": 1005, "name": "INV/2026/0005", "partner_id": 5, "partner": "Dubai Digital LLC", "amount_total": 45000.00, "amount_due": 22500.00, "state": "posted", "payment_state": "partial", "invoice_date": "2026-01-20", "due_date": "2026-02-20", "currency": "AED", "type": "out_invoice"},
    {"id": 1006, "name": "INV/2026/0006", "partner_id": 6, "partner": "Ali Hassan Trading", "amount_total": 8900.00, "amount_due": 0, "state": "posted", "payment_state": "paid", "invoice_date": "2026-01-28", "due_date": "2026-02-28", "currency": "PKR", "type": "out_invoice"},
    {"id": 1007, "name": "INV/2026/0007", "partner_id": 10, "partner": "Fatima Enterprises", "amount_total": 15600.00, "amount_due": 15600.00, "state": "posted", "payment_state": "not_paid", "invoice_date": "2026-02-08", "due_date": "2026-03-08", "currency": "PKR", "type": "out_invoice"},
    {"id": 1008, "name": "INV/2026/0008", "partner_id": 11, "partner": "Berlin Software GmbH", "amount_total": 22000.00, "amount_due": 0, "state": "posted", "payment_state": "paid", "invoice_date": "2026-02-01", "due_date": "2026-03-01", "currency": "EUR", "type": "out_invoice"},
    {"id": 1009, "name": "INV/2026/0009", "partner_id": 12, "partner": "Tokyo Tech Solutions", "amount_total": 31500.00, "amount_due": 31500.00, "state": "draft", "payment_state": "not_paid", "invoice_date": "2026-02-13", "due_date": "2026-03-13", "currency": "JPY", "type": "out_invoice"},
    {"id": 1010, "name": "INV/2026/0010", "partner_id": 5, "partner": "Dubai Digital LLC", "amount_total": 18000.00, "amount_due": 18000.00, "state": "posted", "payment_state": "not_paid", "invoice_date": "2026-02-11", "due_date": "2026-03-11", "currency": "AED", "type": "out_invoice"},
    # Vendor Bills
    {"id": 2001, "name": "BILL/2026/0001", "partner_id": 7, "partner": "AWS Cloud Services", "amount_total": 2340.00, "amount_due": 2340.00, "state": "posted", "payment_state": "not_paid", "invoice_date": "2026-02-01", "due_date": "2026-03-01", "currency": "USD", "type": "in_invoice"},
    {"id": 2002, "name": "BILL/2026/0002", "partner_id": 8, "partner": "Google Cloud Platform", "amount_total": 1850.00, "amount_due": 0, "state": "posted", "payment_state": "paid", "invoice_date": "2026-01-31", "due_date": "2026-02-28", "currency": "USD", "type": "in_invoice"},
    {"id": 2003, "name": "BILL/2026/0003", "partner_id": 9, "partner": "Vercel Inc", "amount_total": 420.00, "amount_due": 420.00, "state": "posted", "payment_state": "not_paid", "invoice_date": "2026-02-05", "due_date": "2026-03-05", "currency": "USD", "type": "in_invoice"},
]

# ============================================================
# DEMO DATA - Sale Orders
# ============================================================
DEMO_ORDERS = [
    {"id": 3001, "name": "SO001", "partner_id": 1, "partner": "Acme Corp", "amount_total": 15000.00, "state": "sale", "date_order": "2026-01-10", "commitment_date": "2026-02-10", "invoice_status": "invoiced", "lines": [{"product": "AI Consultation (1hr)", "qty": 20, "price": 250.00, "subtotal": 5000.00}, {"product": "Cloud Server Setup", "qty": 5, "price": 1500.00, "subtotal": 7500.00}, {"product": "Data Migration Package", "qty": 0.5, "price": 5000.00, "subtotal": 2500.00}]},
    {"id": 3002, "name": "SO002", "partner_id": 2, "partner": "TechStart Inc", "amount_total": 7800.00, "state": "draft", "date_order": "2026-02-08", "commitment_date": "2026-03-08", "invoice_status": "to invoice", "lines": [{"product": "Monthly SaaS License", "qty": 50, "price": 99.00, "subtotal": 4950.00}, {"product": "AI Consultation (1hr)", "qty": 10, "price": 250.00, "subtotal": 2500.00}, {"product": "Support Package", "qty": 1, "price": 350.00, "subtotal": 350.00}]},
    {"id": 3003, "name": "SO003", "partner_id": 3, "partner": "Global Traders Ltd", "amount_total": 22000.00, "state": "sale", "date_order": "2026-02-11", "commitment_date": "2026-03-15", "invoice_status": "to invoice", "lines": [{"product": "Enterprise License", "qty": 1, "price": 15000.00, "subtotal": 15000.00}, {"product": "Cloud Server Setup", "qty": 3, "price": 1500.00, "subtotal": 4500.00}, {"product": "Data Migration Package", "qty": 0.5, "price": 5000.00, "subtotal": 2500.00}]},
    {"id": 3004, "name": "SO004", "partner_id": 5, "partner": "Dubai Digital LLC", "amount_total": 63000.00, "state": "sale", "date_order": "2026-01-20", "commitment_date": "2026-03-01", "invoice_status": "invoiced", "lines": [{"product": "Enterprise License", "qty": 3, "price": 15000.00, "subtotal": 45000.00}, {"product": "Cloud Server Setup", "qty": 10, "price": 1500.00, "subtotal": 15000.00}, {"product": "Support Package", "qty": 6, "price": 500.00, "subtotal": 3000.00}]},
    {"id": 3005, "name": "SO005", "partner_id": 10, "partner": "Fatima Enterprises", "amount_total": 15600.00, "state": "sale", "date_order": "2026-02-08", "commitment_date": "2026-03-10", "invoice_status": "invoiced", "lines": [{"product": "AI Consultation (1hr)", "qty": 40, "price": 250.00, "subtotal": 10000.00}, {"product": "Monthly SaaS License", "qty": 20, "price": 99.00, "subtotal": 1980.00}, {"product": "Custom Development", "qty": 12, "price": 300.00, "subtotal": 3600.00}]},
    {"id": 3006, "name": "SO006", "partner_id": 11, "partner": "Berlin Software GmbH", "amount_total": 22000.00, "state": "done", "date_order": "2026-01-15", "commitment_date": "2026-02-01", "invoice_status": "invoiced", "lines": [{"product": "Enterprise License", "qty": 1, "price": 15000.00, "subtotal": 15000.00}, {"product": "AI Consultation (1hr)", "qty": 20, "price": 250.00, "subtotal": 5000.00}, {"product": "Support Package", "qty": 4, "price": 500.00, "subtotal": 2000.00}]},
    {"id": 3007, "name": "SO007", "partner_id": 12, "partner": "Tokyo Tech Solutions", "amount_total": 31500.00, "state": "draft", "date_order": "2026-02-13", "commitment_date": "2026-04-01", "invoice_status": "no", "lines": [{"product": "Enterprise License", "qty": 2, "price": 15000.00, "subtotal": 30000.00}, {"product": "Cloud Server Setup", "qty": 1, "price": 1500.00, "subtotal": 1500.00}]},
    {"id": 3008, "name": "SO008", "partner_id": 6, "partner": "Ali Hassan Trading", "amount_total": 8900.00, "state": "sale", "date_order": "2026-01-28", "commitment_date": "2026-02-28", "invoice_status": "invoiced", "lines": [{"product": "Monthly SaaS License", "qty": 40, "price": 99.00, "subtotal": 3960.00}, {"product": "AI Consultation (1hr)", "qty": 15, "price": 250.00, "subtotal": 3750.00}, {"product": "Support Package", "qty": 2, "price": 595.00, "subtotal": 1190.00}]},
]

# ============================================================
# DEMO DATA - Products
# ============================================================
DEMO_PRODUCTS = [
    {"id": 1, "name": "AI Consultation (1hr)", "list_price": 250.00, "standard_price": 80.00, "qty_available": 999, "category": "Services", "type": "service", "uom": "Hours", "barcode": "SRV-AI-001"},
    {"id": 2, "name": "Cloud Server Setup", "list_price": 1500.00, "standard_price": 400.00, "qty_available": 50, "category": "Services", "type": "service", "uom": "Units", "barcode": "SRV-CLD-002"},
    {"id": 3, "name": "Monthly SaaS License", "list_price": 99.00, "standard_price": 15.00, "qty_available": 9999, "category": "Subscriptions", "type": "service", "uom": "Units", "barcode": "SUB-SAS-003"},
    {"id": 4, "name": "Data Migration Package", "list_price": 5000.00, "standard_price": 1200.00, "qty_available": 20, "category": "Services", "type": "service", "uom": "Units", "barcode": "SRV-MIG-004"},
    {"id": 5, "name": "Enterprise License", "list_price": 15000.00, "standard_price": 3000.00, "qty_available": 100, "category": "Licenses", "type": "service", "uom": "Units", "barcode": "LIC-ENT-005"},
    {"id": 6, "name": "Support Package (Monthly)", "list_price": 500.00, "standard_price": 120.00, "qty_available": 999, "category": "Support", "type": "service", "uom": "Months", "barcode": "SUP-MTH-006"},
    {"id": 7, "name": "Custom Development (1hr)", "list_price": 300.00, "standard_price": 100.00, "qty_available": 999, "category": "Services", "type": "service", "uom": "Hours", "barcode": "SRV-DEV-007"},
    {"id": 8, "name": "Laptop - Dell XPS 15", "list_price": 1899.00, "standard_price": 1350.00, "qty_available": 12, "category": "Hardware", "type": "product", "uom": "Units", "barcode": "HW-LAP-008"},
    {"id": 9, "name": "Monitor - LG 27\" 4K", "list_price": 449.00, "standard_price": 280.00, "qty_available": 25, "category": "Hardware", "type": "product", "uom": "Units", "barcode": "HW-MON-009"},
    {"id": 10, "name": "Mechanical Keyboard", "list_price": 159.00, "standard_price": 75.00, "qty_available": 40, "category": "Hardware", "type": "product", "uom": "Units", "barcode": "HW-KEY-010"},
]

# ============================================================
# DEMO DATA - Employees (hr.employee)
# ============================================================
DEMO_EMPLOYEES = [
    {"id": 1, "name": "Naveed Qureshi", "job_title": "CEO & Founder", "department": "Management", "email": "qureshinaveedgiaic@gmail.com", "phone": "+92-300-1234567", "work_location": "Karachi Office", "coach": None, "status": "active", "join_date": "2024-01-01"},
    {"id": 2, "name": "Ahmed Khan", "job_title": "Senior Developer", "department": "Engineering", "email": "ahmed.khan@company.pk", "phone": "+92-321-9876543", "work_location": "Karachi Office", "coach": "Naveed Qureshi", "status": "active", "join_date": "2024-03-15"},
    {"id": 3, "name": "Sarah Ali", "job_title": "UI/UX Designer", "department": "Design", "email": "sarah.ali@company.pk", "phone": "+92-333-5551234", "work_location": "Remote", "coach": "Naveed Qureshi", "status": "active", "join_date": "2024-06-01"},
    {"id": 4, "name": "Omar Farooq", "job_title": "DevOps Engineer", "department": "Engineering", "email": "omar.farooq@company.pk", "phone": "+92-312-7778899", "work_location": "Lahore Office", "coach": "Ahmed Khan", "status": "active", "join_date": "2024-08-10"},
    {"id": 5, "name": "Zainab Malik", "job_title": "Marketing Manager", "department": "Marketing", "email": "zainab.malik@company.pk", "phone": "+92-345-1112233", "work_location": "Karachi Office", "coach": "Naveed Qureshi", "status": "active", "join_date": "2025-01-15"},
    {"id": 6, "name": "Hassan Raza", "job_title": "Backend Developer", "department": "Engineering", "email": "hassan.raza@company.pk", "phone": "+92-300-4445566", "work_location": "Remote", "coach": "Ahmed Khan", "status": "active", "join_date": "2025-04-01"},
    {"id": 7, "name": "Ayesha Siddiqui", "job_title": "Accountant", "department": "Finance", "email": "ayesha.s@company.pk", "phone": "+92-311-8889900", "work_location": "Karachi Office", "coach": "Naveed Qureshi", "status": "active", "join_date": "2025-06-15"},
    {"id": 8, "name": "Bilal Ahmed", "job_title": "QA Engineer", "department": "Engineering", "email": "bilal.ahmed@company.pk", "phone": "+92-322-6667788", "work_location": "Karachi Office", "coach": "Ahmed Khan", "status": "active", "join_date": "2025-09-01"},
]

# ============================================================
# DEMO DATA - Purchase Orders (purchase.order)
# ============================================================
DEMO_PURCHASES = [
    {"id": 4001, "name": "PO001", "partner_id": 7, "partner": "AWS Cloud Services", "amount_total": 2340.00, "state": "purchase", "date_order": "2026-01-25", "date_planned": "2026-02-01", "lines": [{"product": "EC2 Instances (Monthly)", "qty": 3, "price": 580.00, "subtotal": 1740.00}, {"product": "S3 Storage (500GB)", "qty": 1, "price": 600.00, "subtotal": 600.00}]},
    {"id": 4002, "name": "PO002", "partner_id": 8, "partner": "Google Cloud Platform", "amount_total": 1850.00, "state": "done", "date_order": "2026-01-20", "date_planned": "2026-02-01", "lines": [{"product": "GKE Cluster", "qty": 1, "price": 1200.00, "subtotal": 1200.00}, {"product": "Cloud SQL", "qty": 1, "price": 650.00, "subtotal": 650.00}]},
    {"id": 4003, "name": "PO003", "partner_id": 9, "partner": "Vercel Inc", "amount_total": 420.00, "state": "purchase", "date_order": "2026-02-01", "date_planned": "2026-02-05", "lines": [{"product": "Pro Plan (Annual)", "qty": 1, "price": 240.00, "subtotal": 240.00}, {"product": "Edge Functions Addon", "qty": 1, "price": 180.00, "subtotal": 180.00}]},
    {"id": 4004, "name": "PO004", "partner_id": 7, "partner": "AWS Cloud Services", "amount_total": 5100.00, "state": "draft", "date_order": "2026-02-12", "date_planned": "2026-03-01", "lines": [{"product": "Reserved Instances (1yr)", "qty": 2, "price": 2200.00, "subtotal": 4400.00}, {"product": "CloudFront CDN", "qty": 1, "price": 700.00, "subtotal": 700.00}]},
]

# ============================================================
# DEMO DATA - CRM Leads / Opportunities (crm.lead)
# ============================================================
DEMO_LEADS = [
    {"id": 5001, "name": "AI Automation for Manufacturing", "partner": "Acme Corp", "email": "cto@acme.com", "phone": "+1-555-0101", "stage": "Qualified", "expected_revenue": 75000.00, "probability": 60, "source": "Website", "salesperson": "Naveed Qureshi", "date_deadline": "2026-03-15", "priority": "2"},
    {"id": 5002, "name": "SaaS Platform Integration", "partner": "TechStart Inc", "email": "ceo@techstart.io", "phone": "+1-555-0202", "stage": "Proposition", "expected_revenue": 42000.00, "probability": 40, "source": "LinkedIn", "salesperson": "Zainab Malik", "date_deadline": "2026-03-30", "priority": "1"},
    {"id": 5003, "name": "Enterprise ERP Migration", "partner": "Dubai Digital LLC", "email": "vp@dubaidigital.ae", "phone": "+971-4-555-9999", "stage": "Won", "expected_revenue": 120000.00, "probability": 100, "source": "Referral", "salesperson": "Naveed Qureshi", "date_deadline": "2026-02-01", "priority": "3"},
    {"id": 5004, "name": "Cloud Infrastructure Setup", "partner": "Berlin Software GmbH", "email": "cto@berlinsw.de", "phone": "+49-30-12345678", "stage": "Qualified", "expected_revenue": 35000.00, "probability": 55, "source": "Conference", "salesperson": "Naveed Qureshi", "date_deadline": "2026-04-01", "priority": "2"},
    {"id": 5005, "name": "Custom Chatbot Development", "partner": "Fatima Enterprises", "email": "fatima@fenterprises.pk", "phone": "+92-42-7890123", "stage": "New", "expected_revenue": 28000.00, "probability": 20, "source": "Email Campaign", "salesperson": "Zainab Malik", "date_deadline": "2026-04-15", "priority": "1"},
    {"id": 5006, "name": "Data Analytics Dashboard", "partner": "Tokyo Tech Solutions", "email": "pm@tokyotech.jp", "phone": "+81-3-1234-5678", "stage": "Proposition", "expected_revenue": 55000.00, "probability": 45, "source": "Partner", "salesperson": "Naveed Qureshi", "date_deadline": "2026-05-01", "priority": "2"},
    {"id": 5007, "name": "Mobile App Development", "partner": "Ali Hassan Trading", "email": "ali@ahtrading.pk", "phone": "+92-21-3456789", "stage": "Qualified", "expected_revenue": 18000.00, "probability": 65, "source": "Website", "salesperson": "Zainab Malik", "date_deadline": "2026-03-20", "priority": "1"},
    {"id": 5008, "name": "AI Employee System License", "partner": "Global Traders Ltd", "email": "it@globaltraders.com", "phone": "+44-20-7946-0958", "stage": "New", "expected_revenue": 95000.00, "probability": 15, "source": "Cold Call", "salesperson": "Naveed Qureshi", "date_deadline": "2026-05-30", "priority": "3"},
]

# ============================================================
# DEMO DATA - Expenses (hr.expense)
# ============================================================
DEMO_EXPENSES = [
    {"id": 6001, "name": "AWS Monthly Bill - January", "employee": "Omar Farooq", "amount": 2340.00, "state": "approved", "date": "2026-02-01", "category": "Cloud Services", "description": "AWS infrastructure costs for January 2026"},
    {"id": 6002, "name": "Google Cloud - January", "employee": "Omar Farooq", "amount": 1850.00, "state": "done", "date": "2026-01-31", "category": "Cloud Services", "description": "GCP services for January 2026"},
    {"id": 6003, "name": "Team Dinner - Sprint Celebration", "employee": "Naveed Qureshi", "amount": 450.00, "state": "approved", "date": "2026-02-07", "category": "Meals & Entertainment", "description": "Sprint 14 celebration dinner with team"},
    {"id": 6004, "name": "Laptop - New Developer", "employee": "Ahmed Khan", "amount": 1899.00, "state": "submitted", "date": "2026-02-10", "category": "Equipment", "description": "Dell XPS 15 for new hire Bilal Ahmed"},
    {"id": 6005, "name": "Conference Tickets - DevCon 2026", "employee": "Zainab Malik", "amount": 1200.00, "state": "draft", "date": "2026-02-12", "category": "Training & Conferences", "description": "2 tickets for DevCon 2026 in Dubai"},
    {"id": 6006, "name": "Office Supplies - Feb", "employee": "Ayesha Siddiqui", "amount": 320.00, "state": "approved", "date": "2026-02-05", "category": "Office Supplies", "description": "Monthly office supplies order"},
    {"id": 6007, "name": "Vercel Pro Subscription", "employee": "Hassan Raza", "amount": 420.00, "state": "approved", "date": "2026-02-05", "category": "Software", "description": "Annual Vercel Pro plan"},
    {"id": 6008, "name": "Uber - Client Meeting Travel", "employee": "Naveed Qureshi", "amount": 85.00, "state": "submitted", "date": "2026-02-13", "category": "Travel", "description": "Transportation to client meeting at Acme Corp"},
]

# ============================================================
# DEMO DATA - Attendance (hr.attendance)
# ============================================================
DEMO_ATTENDANCE = [
    {"id": 7001, "employee": "Naveed Qureshi", "check_in": "2026-02-13 09:00:00", "check_out": "2026-02-13 18:30:00", "worked_hours": 9.5},
    {"id": 7002, "employee": "Ahmed Khan", "check_in": "2026-02-13 09:15:00", "check_out": "2026-02-13 19:00:00", "worked_hours": 9.75},
    {"id": 7003, "employee": "Sarah Ali", "check_in": "2026-02-13 10:00:00", "check_out": "2026-02-13 18:00:00", "worked_hours": 8.0},
    {"id": 7004, "employee": "Omar Farooq", "check_in": "2026-02-13 08:30:00", "check_out": "2026-02-13 17:30:00", "worked_hours": 9.0},
    {"id": 7005, "employee": "Zainab Malik", "check_in": "2026-02-13 09:30:00", "check_out": None, "worked_hours": None},
    {"id": 7006, "employee": "Hassan Raza", "check_in": "2026-02-13 11:00:00", "check_out": "2026-02-13 20:00:00", "worked_hours": 9.0},
    {"id": 7007, "employee": "Ayesha Siddiqui", "check_in": "2026-02-13 09:00:00", "check_out": "2026-02-13 17:00:00", "worked_hours": 8.0},
    {"id": 7008, "employee": "Bilal Ahmed", "check_in": "2026-02-13 09:45:00", "check_out": "2026-02-13 18:45:00", "worked_hours": 9.0},
]

# ============================================================
# DEMO DATA - Leave Requests (hr.leave)
# ============================================================
DEMO_LEAVES = [
    {"id": 8001, "employee": "Sarah Ali", "type": "Annual Leave", "date_from": "2026-02-17", "date_to": "2026-02-21", "days": 5, "state": "validate", "reason": "Family vacation"},
    {"id": 8002, "employee": "Hassan Raza", "type": "Sick Leave", "date_from": "2026-02-10", "date_to": "2026-02-10", "days": 1, "state": "validate", "reason": "Flu"},
    {"id": 8003, "employee": "Omar Farooq", "type": "Annual Leave", "date_from": "2026-02-24", "date_to": "2026-02-28", "days": 5, "state": "confirm", "reason": "Wedding in family"},
    {"id": 8004, "employee": "Bilal Ahmed", "type": "Work From Home", "date_from": "2026-02-14", "date_to": "2026-02-14", "days": 1, "state": "validate", "reason": "Internet maintenance at office"},
    {"id": 8005, "employee": "Zainab Malik", "type": "Annual Leave", "date_from": "2026-03-01", "date_to": "2026-03-05", "days": 5, "state": "draft", "reason": "Conference travel + personal days"},
]

# ============================================================
# DEMO DATA - Projects (project.project / project.task)
# ============================================================
DEMO_PROJECTS = [
    {"id": 9001, "name": "Personal AI Employee", "manager": "Naveed Qureshi", "status": "in_progress", "partner": None, "date_start": "2024-01-01", "deadline": "2026-06-30", "task_count": 45, "completed_tasks": 38, "progress": 84},
    {"id": 9002, "name": "Dubai Digital - ERP Migration", "manager": "Ahmed Khan", "status": "in_progress", "partner": "Dubai Digital LLC", "date_start": "2026-01-15", "deadline": "2026-04-30", "task_count": 32, "completed_tasks": 12, "progress": 37},
    {"id": 9003, "name": "Berlin SW - Cloud Setup", "manager": "Omar Farooq", "status": "in_progress", "partner": "Berlin Software GmbH", "date_start": "2026-02-01", "deadline": "2026-03-31", "task_count": 18, "completed_tasks": 5, "progress": 28},
    {"id": 9004, "name": "Website Redesign", "manager": "Sarah Ali", "status": "in_progress", "partner": None, "date_start": "2026-01-20", "deadline": "2026-03-15", "task_count": 22, "completed_tasks": 15, "progress": 68},
    {"id": 9005, "name": "Mobile App v2", "manager": "Hassan Raza", "status": "planned", "partner": "Ali Hassan Trading", "date_start": "2026-03-01", "deadline": "2026-06-30", "task_count": 0, "completed_tasks": 0, "progress": 0},
]

# ============================================================
# DEMO DATA - Payments (account.payment)
# ============================================================
DEMO_PAYMENTS = [
    {"id": 10001, "name": "PAY/2026/0001", "partner": "Acme Corp", "amount": 5000.00, "state": "posted", "date": "2026-02-01", "payment_type": "inbound", "journal": "Bank", "method": "Wire Transfer"},
    {"id": 10002, "name": "PAY/2026/0002", "partner": "Acme Corp", "amount": 8750.00, "state": "posted", "date": "2026-02-12", "payment_type": "inbound", "journal": "Bank", "method": "Wire Transfer"},
    {"id": 10003, "name": "PAY/2026/0003", "partner": "Dubai Digital LLC", "amount": 22500.00, "state": "posted", "date": "2026-02-05", "payment_type": "inbound", "journal": "Bank", "method": "Check"},
    {"id": 10004, "name": "PAY/2026/0004", "partner": "Ali Hassan Trading", "amount": 8900.00, "state": "posted", "date": "2026-02-03", "payment_type": "inbound", "journal": "Bank", "method": "Online Payment"},
    {"id": 10005, "name": "PAY/2026/0005", "partner": "Berlin Software GmbH", "amount": 22000.00, "state": "posted", "date": "2026-02-08", "payment_type": "inbound", "journal": "Bank", "method": "Wire Transfer"},
    {"id": 10006, "name": "PAY/2026/0006", "partner": "Google Cloud Platform", "amount": 1850.00, "state": "posted", "date": "2026-02-02", "payment_type": "outbound", "journal": "Bank", "method": "Credit Card"},
    {"id": 10007, "name": "PAY/2026/0007", "partner": "AWS Cloud Services", "amount": 2340.00, "state": "draft", "date": "2026-02-14", "payment_type": "outbound", "journal": "Bank", "method": "Wire Transfer"},
]


# ============================================================
# HTTP Handler
# ============================================================
class OdooHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[Odoo Mock] {args[0]}")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        if self.path == "/" or self.path == "/web":
            self.send_html(self._dashboard_html())
        elif self.path == "/web/database/selector":
            self.send_json({"databases": ["ai_employee_db"]})
        elif self.path == "/web/session/get_session_info":
            self.send_json(self._session_info())
        elif self.path.startswith("/api/"):
            self._handle_api(self.path)
        else:
            self.send_json({"status": "ok", "server": "Odoo 17.0 (Mock)"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        try:
            data = json.loads(body)
        except:
            data = {}

        if self.path == "/web/session/authenticate":
            self.send_json({
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "uid": 2,
                    "session_id": "mock_session_" + str(random.randint(1000, 9999)),
                    "db": "ai_employee_db",
                    "username": "admin",
                    "company_id": 1,
                    "partner_id": 4,
                }
            })
        elif self.path == "/web/dataset/call_kw" or self.path == "/web/dataset/call":
            self._handle_rpc(data)
        elif self.path == "/jsonrpc" or self.path == "/xmlrpc/2/common":
            self.send_json({
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "server_version": "17.0",
                    "server_version_info": [17, 0, 0, "final", 0, ""],
                    "server_serie": "17.0",
                    "protocol_version": 1,
                }
            })
        elif self.path == "/xmlrpc/2/object":
            self._handle_xmlrpc_object(data)
        else:
            self.send_json({"jsonrpc": "2.0", "result": True})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _session_info(self):
        return {
            "uid": 2, "username": "admin", "name": "Administrator",
            "db": "ai_employee_db", "company_id": 1, "server_version": "17.0",
        }

    def _handle_api(self, path):
        if "/partners" in path:
            self.send_json({"data": DEMO_PARTNERS, "count": len(DEMO_PARTNERS)})
        elif "/invoices" in path:
            self.send_json({"data": DEMO_INVOICES, "count": len(DEMO_INVOICES)})
        elif "/orders" in path and "purchase" not in path:
            self.send_json({"data": DEMO_ORDERS, "count": len(DEMO_ORDERS)})
        elif "/purchase" in path:
            self.send_json({"data": DEMO_PURCHASES, "count": len(DEMO_PURCHASES)})
        elif "/products" in path:
            self.send_json({"data": DEMO_PRODUCTS, "count": len(DEMO_PRODUCTS)})
        elif "/employees" in path:
            self.send_json({"data": DEMO_EMPLOYEES, "count": len(DEMO_EMPLOYEES)})
        elif "/leads" in path or "/crm" in path:
            self.send_json({"data": DEMO_LEADS, "count": len(DEMO_LEADS)})
        elif "/expenses" in path:
            self.send_json({"data": DEMO_EXPENSES, "count": len(DEMO_EXPENSES)})
        elif "/attendance" in path:
            self.send_json({"data": DEMO_ATTENDANCE, "count": len(DEMO_ATTENDANCE)})
        elif "/leaves" in path:
            self.send_json({"data": DEMO_LEAVES, "count": len(DEMO_LEAVES)})
        elif "/projects" in path:
            self.send_json({"data": DEMO_PROJECTS, "count": len(DEMO_PROJECTS)})
        elif "/payments" in path:
            self.send_json({"data": DEMO_PAYMENTS, "count": len(DEMO_PAYMENTS)})
        elif "/summary" in path or "/dashboard" in path:
            self.send_json(self._full_summary())
        else:
            self.send_json({"status": "ok", "available_endpoints": [
                "/api/partners", "/api/invoices", "/api/orders", "/api/purchase",
                "/api/products", "/api/employees", "/api/leads", "/api/crm",
                "/api/expenses", "/api/attendance", "/api/leaves", "/api/projects",
                "/api/payments", "/api/summary", "/api/dashboard"
            ]})

    def _full_summary(self):
        customer_invoices = [i for i in DEMO_INVOICES if i["type"] == "out_invoice"]
        vendor_bills = [i for i in DEMO_INVOICES if i["type"] == "in_invoice"]
        return {
            "company": "AI Employee Corp",
            "currency": "USD",
            "date": datetime.now().isoformat(),
            "revenue": {
                "total_invoiced": sum(i["amount_total"] for i in customer_invoices),
                "total_paid": sum(i["amount_total"] for i in customer_invoices if i["payment_state"] == "paid"),
                "total_due": sum(i["amount_due"] for i in customer_invoices),
                "overdue": sum(1 for i in customer_invoices if i["amount_due"] > 0 and i["due_date"] < "2026-02-14"),
            },
            "expenses": {
                "total_bills": sum(b["amount_total"] for b in vendor_bills),
                "unpaid_bills": sum(b["amount_due"] for b in vendor_bills),
                "employee_expenses": sum(e["amount"] for e in DEMO_EXPENSES),
                "pending_approval": sum(1 for e in DEMO_EXPENSES if e["state"] in ("draft", "submitted")),
            },
            "sales": {
                "total_orders": len(DEMO_ORDERS),
                "confirmed": sum(1 for o in DEMO_ORDERS if o["state"] in ("sale", "done")),
                "draft": sum(1 for o in DEMO_ORDERS if o["state"] == "draft"),
                "total_value": sum(o["amount_total"] for o in DEMO_ORDERS),
            },
            "crm": {
                "total_leads": len(DEMO_LEADS),
                "won": sum(1 for l in DEMO_LEADS if l["stage"] == "Won"),
                "pipeline_value": sum(l["expected_revenue"] for l in DEMO_LEADS if l["stage"] != "Won"),
                "avg_probability": round(sum(l["probability"] for l in DEMO_LEADS) / len(DEMO_LEADS), 1),
            },
            "hr": {
                "total_employees": len(DEMO_EMPLOYEES),
                "active": sum(1 for e in DEMO_EMPLOYEES if e["status"] == "active"),
                "checked_in_today": sum(1 for a in DEMO_ATTENDANCE if a["check_out"] is None),
                "pending_leaves": sum(1 for l in DEMO_LEAVES if l["state"] in ("draft", "confirm")),
            },
            "projects": {
                "total": len(DEMO_PROJECTS),
                "in_progress": sum(1 for p in DEMO_PROJECTS if p["status"] == "in_progress"),
                "avg_progress": round(sum(p["progress"] for p in DEMO_PROJECTS) / len(DEMO_PROJECTS), 1),
            },
            "partners": {
                "total": len(DEMO_PARTNERS),
                "customers": sum(1 for p in DEMO_PARTNERS if p["type"] == "customer"),
                "vendors": sum(1 for p in DEMO_PARTNERS if p["type"] == "vendor"),
            },
            "payments": {
                "received": sum(p["amount"] for p in DEMO_PAYMENTS if p["payment_type"] == "inbound" and p["state"] == "posted"),
                "sent": sum(p["amount"] for p in DEMO_PAYMENTS if p["payment_type"] == "outbound" and p["state"] == "posted"),
                "pending": sum(p["amount"] for p in DEMO_PAYMENTS if p["state"] == "draft"),
            }
        }

    def _handle_rpc(self, data):
        params = data.get("params", {})
        model = params.get("model", "")
        model_map = {
            "res.partner": DEMO_PARTNERS,
            "account.move": DEMO_INVOICES,
            "sale.order": DEMO_ORDERS,
            "purchase.order": DEMO_PURCHASES,
            "product.product": DEMO_PRODUCTS,
            "product.template": DEMO_PRODUCTS,
            "hr.employee": DEMO_EMPLOYEES,
            "crm.lead": DEMO_LEADS,
            "hr.expense": DEMO_EXPENSES,
            "hr.attendance": DEMO_ATTENDANCE,
            "hr.leave": DEMO_LEAVES,
            "project.project": DEMO_PROJECTS,
            "account.payment": DEMO_PAYMENTS,
        }
        result = model_map.get(model, [])
        self.send_json({"jsonrpc": "2.0", "id": data.get("id"), "result": result})

    def _handle_xmlrpc_object(self, data):
        self.send_json({"jsonrpc": "2.0", "id": data.get("id"), "result": 2})

    def _dashboard_html(self):
        s = self._full_summary()
        return f'''<!DOCTYPE html>
<html><head><title>Odoo 17 - AI Employee ERP</title>
<style>
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
.header {{ background: #714B67; color: #fff; padding: 20px 30px; }}
.header h1 {{ margin: 0; font-size: 1.4em; }}
.header p {{ margin: 5px 0 0; opacity: 0.8; }}
.container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }}
.card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.card h3 {{ margin: 0 0 15px; color: #714B67; font-size: 1em; border-bottom: 2px solid #714B67; padding-bottom: 8px; }}
.stat {{ display: flex; justify-content: space-between; margin: 8px 0; }}
.stat .label {{ color: #666; }}
.stat .value {{ font-weight: 600; color: #333; }}
.green {{ color: #28a745 !important; }}
.red {{ color: #dc3545 !important; }}
.orange {{ color: #fd7e14 !important; }}
.api-list {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.api-list h3 {{ color: #714B67; margin: 0 0 10px; }}
.api-list a {{ display: inline-block; margin: 4px; padding: 6px 12px; background: #714B67; color: #fff; border-radius: 4px; text-decoration: none; font-size: 0.85em; }}
.api-list a:hover {{ background: #5a3a52; }}
</style></head>
<body>
<div class="header"><h1>Odoo 17 (Mock) - AI Employee ERP</h1><p>Database: ai_employee_db | User: admin | {datetime.now().strftime("%Y-%m-%d %H:%M")}</p></div>
<div class="container">
<div class="grid">
  <div class="card"><h3>Revenue</h3>
    <div class="stat"><span class="label">Total Invoiced</span><span class="value">${s["revenue"]["total_invoiced"]:,.2f}</span></div>
    <div class="stat"><span class="label">Paid</span><span class="value green">${s["revenue"]["total_paid"]:,.2f}</span></div>
    <div class="stat"><span class="label">Amount Due</span><span class="value orange">${s["revenue"]["total_due"]:,.2f}</span></div>
    <div class="stat"><span class="label">Overdue Invoices</span><span class="value red">{s["revenue"]["overdue"]}</span></div>
  </div>
  <div class="card"><h3>Sales</h3>
    <div class="stat"><span class="label">Total Orders</span><span class="value">{s["sales"]["total_orders"]}</span></div>
    <div class="stat"><span class="label">Confirmed</span><span class="value green">{s["sales"]["confirmed"]}</span></div>
    <div class="stat"><span class="label">Draft</span><span class="value orange">{s["sales"]["draft"]}</span></div>
    <div class="stat"><span class="label">Total Value</span><span class="value">${s["sales"]["total_value"]:,.2f}</span></div>
  </div>
  <div class="card"><h3>CRM Pipeline</h3>
    <div class="stat"><span class="label">Total Leads</span><span class="value">{s["crm"]["total_leads"]}</span></div>
    <div class="stat"><span class="label">Won</span><span class="value green">{s["crm"]["won"]}</span></div>
    <div class="stat"><span class="label">Pipeline Value</span><span class="value">${s["crm"]["pipeline_value"]:,.2f}</span></div>
    <div class="stat"><span class="label">Avg Probability</span><span class="value">{s["crm"]["avg_probability"]}%</span></div>
  </div>
  <div class="card"><h3>Expenses</h3>
    <div class="stat"><span class="label">Vendor Bills</span><span class="value">${s["expenses"]["total_bills"]:,.2f}</span></div>
    <div class="stat"><span class="label">Unpaid Bills</span><span class="value red">${s["expenses"]["unpaid_bills"]:,.2f}</span></div>
    <div class="stat"><span class="label">Employee Expenses</span><span class="value">${s["expenses"]["employee_expenses"]:,.2f}</span></div>
    <div class="stat"><span class="label">Pending Approval</span><span class="value orange">{s["expenses"]["pending_approval"]}</span></div>
  </div>
  <div class="card"><h3>HR / Team</h3>
    <div class="stat"><span class="label">Employees</span><span class="value">{s["hr"]["total_employees"]}</span></div>
    <div class="stat"><span class="label">Active</span><span class="value green">{s["hr"]["active"]}</span></div>
    <div class="stat"><span class="label">Checked In Now</span><span class="value">{s["hr"]["checked_in_today"]}</span></div>
    <div class="stat"><span class="label">Pending Leaves</span><span class="value orange">{s["hr"]["pending_leaves"]}</span></div>
  </div>
  <div class="card"><h3>Payments</h3>
    <div class="stat"><span class="label">Received</span><span class="value green">${s["payments"]["received"]:,.2f}</span></div>
    <div class="stat"><span class="label">Sent</span><span class="value red">${s["payments"]["sent"]:,.2f}</span></div>
    <div class="stat"><span class="label">Pending</span><span class="value orange">${s["payments"]["pending"]:,.2f}</span></div>
  </div>
  <div class="card"><h3>Projects</h3>
    <div class="stat"><span class="label">Total</span><span class="value">{s["projects"]["total"]}</span></div>
    <div class="stat"><span class="label">In Progress</span><span class="value green">{s["projects"]["in_progress"]}</span></div>
    <div class="stat"><span class="label">Avg Progress</span><span class="value">{s["projects"]["avg_progress"]}%</span></div>
  </div>
  <div class="card"><h3>Partners</h3>
    <div class="stat"><span class="label">Total</span><span class="value">{s["partners"]["total"]}</span></div>
    <div class="stat"><span class="label">Customers</span><span class="value green">{s["partners"]["customers"]}</span></div>
    <div class="stat"><span class="label">Vendors</span><span class="value">{s["partners"]["vendors"]}</span></div>
  </div>
</div>
<div class="api-list"><h3>API Endpoints</h3>
<a href="/api/summary">/api/summary</a> <a href="/api/partners">/api/partners</a>
<a href="/api/invoices">/api/invoices</a> <a href="/api/orders">/api/orders</a>
<a href="/api/purchase">/api/purchase</a> <a href="/api/products">/api/products</a>
<a href="/api/employees">/api/employees</a> <a href="/api/leads">/api/leads</a>
<a href="/api/expenses">/api/expenses</a> <a href="/api/attendance">/api/attendance</a>
<a href="/api/leaves">/api/leaves</a> <a href="/api/projects">/api/projects</a>
<a href="/api/payments">/api/payments</a>
</div></div></body></html>'''


def main():
    host = "0.0.0.0"
    port = 8069
    server = HTTPServer((host, port), OdooHandler)
    print(f"Mock Odoo 17 server running on http://{host}:{port}")
    print(f"  Database: ai_employee_db | User: admin")
    print(f"  Data loaded:")
    print(f"    Partners:   {len(DEMO_PARTNERS)} (customers + vendors)")
    print(f"    Invoices:   {len(DEMO_INVOICES)} (customer invoices + vendor bills)")
    print(f"    Sale Orders:{len(DEMO_ORDERS)}")
    print(f"    Purchases:  {len(DEMO_PURCHASES)}")
    print(f"    Products:   {len(DEMO_PRODUCTS)}")
    print(f"    Employees:  {len(DEMO_EMPLOYEES)}")
    print(f"    CRM Leads:  {len(DEMO_LEADS)}")
    print(f"    Expenses:   {len(DEMO_EXPENSES)}")
    print(f"    Attendance: {len(DEMO_ATTENDANCE)}")
    print(f"    Leaves:     {len(DEMO_LEAVES)}")
    print(f"    Projects:   {len(DEMO_PROJECTS)}")
    print(f"    Payments:   {len(DEMO_PAYMENTS)}")
    print(f"  Endpoints: /api/summary, /api/partners, /api/invoices, /api/orders, etc.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock Odoo server...")
        server.server_close()


if __name__ == "__main__":
    main()
