"""Printable record export; uses stored snapshots, never recalculates tax."""
from html import escape

from app.models import Booking, Invoice


def printable_invoice(invoice: Invoice, booking: Booking) -> str:
    fields = [
        ('Invoice', invoice.invoice_number), ('Booking', booking.public_id),
        ('Bill to', invoice.legal_name), ('GSTIN supplied by customer', invoice.gstin or 'Not supplied'),
        ('Billing address', invoice.billing_address),
        ('Stored taxable amount (INR)', invoice.taxable_amount),
        ('Stored tax rate (%)', invoice.tax_percent), ('Stored tax amount (INR)', invoice.tax_amount),
        ('Stored total (INR)', invoice.total_amount),
        ('Issued at (UTC)', invoice.issued_at.isoformat() if invoice.issued_at else 'Not recorded'),
    ]
    rows = ''.join(f'<tr><th>{escape(label)}</th><td>{escape(str(value))}</td></tr>' for label, value in fields)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
            '<title>TransivoX booking invoice record</title><style>body{font:16px system-ui;margin:2rem;max-width:900px}'
            'table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;border:1px solid #ddd;overflow-wrap:anywhere}'
            'td{white-space:pre-wrap}@media print{body{margin:0}}</style></head><body>'
            '<h1>TransivoX booking invoice record</h1><p>Issued record export. This document is not proof of payment.</p>'
            f'<table>{rows}</table><p>Use your browser Print → Save as PDF for a printable copy. '
            'Issuer details and statutory invoice requirements require approved business/tax configuration.</p></body></html>')
