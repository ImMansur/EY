# document_generator_enhanced.py
"""
AI-Generated Document Generator for Ticket Auto-Closure
Creates realistic-looking documents even with limited/partial invoice data.
Documents are AI-generated substitutes, not actual official invoices.
"""

import os
from datetime import datetime
from weasyprint import HTML
from jinja2 import Template


def generate_invoice_copy_pdf(invoice_data: dict, ticket_description: str = "", output_dir: str = "temp_docs") -> str | None:
    """
    Generate AI-generated invoice copy substitute.
    Works with whatever data is available - fills gaps intelligently.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        inv_num = str(invoice_data.get("Invoice Number", "UNKNOWN")).replace("/", "-")
        output_filename = f"Invoice_Copy_{inv_num}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        # Smart data extraction with fallbacks
        invoice_number = invoice_data.get("Invoice Number", "N/A")
        invoice_amount = invoice_data.get("Invoice Amount")
        if invoice_amount:
            try:
                amount_display = f"${float(invoice_amount):,.2f}"
            except:
                amount_display = str(invoice_amount)
        else:
            amount_display = "Contact AP/AR for details"
        
        # Get dates - handle various formats
        invoice_date = str(invoice_data.get("Invoice Date", ""))[:10] if invoice_data.get("Invoice Date") else "N/A"
        due_date = str(invoice_data.get("Due Date", ""))[:10] if invoice_data.get("Due Date") else "N/A"
        
        # Entity info (vendor or customer)
        vendor_name = invoice_data.get("Vendor Name")
        customer_name = invoice_data.get("Customer Name")
        entity_name = vendor_name or customer_name or "N/A"
        entity_id = invoice_data.get("Vendor ID") or invoice_data.get("Customer ID") or "N/A"
        entity_type = "Vendor" if vendor_name else "Customer" if customer_name else "Entity"
        
        po_number = invoice_data.get("PO Number", "N/A")
        payment_status = invoice_data.get("Payment Status", "N/A")

        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice Copy - AI Generated</title>
            <style>
                @page { size: A4; margin: 2cm; }
                body {
                    font-family: Arial, Helvetica, sans-serif;
                    color: #2e2e38;
                    line-height: 1.6;
                    font-size: 11pt;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #ffe600;
                    padding-bottom: 20px;
                }
                .ey-logo {
                    font-size: 48pt;
                    font-weight: bold;
                    color: #2e2e38;
                    background: #ffe600;
                    display: inline-block;
                    padding: 10px 25px;
                    border-radius: 8px;
                }
                .doc-type {
                    color: #2e2e38;
                    font-size: 24pt;
                    font-weight: bold;
                    margin-top: 15px;
                }
                .ai-badge {
                    background: #e8f4fd;
                    border: 2px solid #0066cc;
                    color: #0066cc;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-size: 10pt;
                    display: inline-block;
                    margin-top: 10px;
                    font-weight: bold;
                }
                .invoice-details {
                    background: #f8fafc;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 25px;
                    margin: 25px 0;
                }
                .detail-row {
                    display: flex;
                    padding: 12px 0;
                    border-bottom: 1px solid #e2e8f0;
                }
                .detail-label {
                    font-weight: bold;
                    width: 40%;
                    color: #64748b;
                }
                .detail-value {
                    width: 60%;
                    color: #2e2e38;
                }
                .amount-box {
                    background: #fff7cc;
                    border: 3px solid #ffe600;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px;
                    margin: 25px 0;
                }
                .amount-label {
                    font-size: 12pt;
                    color: #64748b;
                    margin-bottom: 5px;
                }
                .amount-value {
                    font-size: 32pt;
                    font-weight: bold;
                    color: #2e2e38;
                }
                .disclaimer {
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 25px 0;
                    font-size: 10pt;
                    color: #856404;
                }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    font-size: 9pt;
                    color: #94a3b8;
                    border-top: 1px solid #e2e8f0;
                    padding-top: 15px;
                }
                .generated-info {
                    font-style: italic;
                    color: #64748b;
                    font-size: 9pt;
                    text-align: right;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="ey-logo">EY</div>
                <div class="doc-type">Invoice Copy</div>
                <div class="ai-badge">🤖 AI-Generated Document</div>
            </div>

            <div class="generated-info">
                Generated: {{ generated_at }}<br>
                Reference: {{ invoice_number }}
            </div>

            <div class="amount-box">
                <div class="amount-label">Invoice Amount</div>
                <div class="amount-value">{{ amount }}</div>
            </div>

            <div class="invoice-details">
                <div class="detail-row">
                    <div class="detail-label">Invoice Number:</div>
                    <div class="detail-value">{{ invoice_number }}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Invoice Date:</div>
                    <div class="detail-value">{{ invoice_date }}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Due Date:</div>
                    <div class="detail-value">{{ due_date }}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">{{ entity_type }}:</div>
                    <div class="detail-value">{{ entity_name }} (ID: {{ entity_id }})</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">PO Number:</div>
                    <div class="detail-value">{{ po_number }}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Payment Status:</div>
                    <div class="detail-value">{{ payment_status }}</div>
                </div>
            </div>

            <div class="disclaimer">
                <strong>⚠️ Important Notice:</strong><br>
                This is an AI-generated document created for your convenience based on available system data. 
                This is NOT an official invoice copy. For official invoices, payment receipts, or tax purposes, 
                please contact your AP/AR team directly to request the original document.
            </div>

            <div class="footer">
                EY Query Management System – AI Agent<br>
                This document was automatically generated in response to: "{{ ticket_description }}"<br>
                For verification or official documentation, please contact your assigned team.
            </div>
        </body>
        </html>
        """

        template = Template(template_html)
        
        render_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_number": invoice_number,
            "amount": amount_display,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "entity_name": entity_name,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "po_number": po_number,
            "payment_status": payment_status,
            "ticket_description": ticket_description[:100] if ticket_description else "Invoice information request"
        }

        html_content = template.render(**render_data)
        HTML(string=html_content).write_pdf(output_path)

        if os.path.exists(output_path):
            print(f"✓ AI-generated invoice copy created: {output_path}")
            return output_path
        return None

    except Exception as e:
        print(f"✗ Invoice copy generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def generate_payment_confirmation_pdf(invoice_data: dict, ticket_description: str = "", output_dir: str = "temp_docs") -> str | None:
    """
    Generate AI-generated payment confirmation document.
    Works with partial data - provides what's available.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        inv_num = str(invoice_data.get("Invoice Number", "UNKNOWN")).replace("/", "-")
        output_filename = f"Payment_Confirmation_{inv_num}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        # Smart data extraction
        invoice_number = invoice_data.get("Invoice Number", "N/A")
        payment_status = str(invoice_data.get("Payment Status", "Unknown")).strip()
        
        invoice_amount = invoice_data.get("Invoice Amount")
        if invoice_amount:
            try:
                amount_display = f"${float(invoice_amount):,.2f}"
            except:
                amount_display = str(invoice_amount)
        else:
            amount_display = "Amount not available"
        
        # Determine status color and message
        if payment_status.lower() == "paid":
            status_color = "#d4edda"
            status_border = "#28a745"
            status_text_color = "#155724"
            status_icon = "✓"
            status_message = "Payment has been processed successfully"
        elif payment_status.lower() == "unpaid":
            status_color = "#fff3cd"
            status_border = "#ffc107"
            status_text_color = "#856404"
            status_icon = "⏳"
            status_message = "Payment is pending"
        else:
            status_color = "#e8f4fd"
            status_border = "#0066cc"
            status_text_color = "#004085"
            status_icon = "ℹ"
            status_message = "Payment status information"
        
        due_date = str(invoice_data.get("Due Date", ""))[:10] if invoice_data.get("Due Date") else "N/A"
        clearing_date = str(invoice_data.get("Clearing Date", ""))[:10] if invoice_data.get("Clearing Date") else "Not available"
        
        entity_name = invoice_data.get("Vendor Name") or invoice_data.get("Customer Name") or "N/A"

        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Payment Confirmation</title>
            <style>
                @page { size: A4; margin: 2cm; }
                body {
                    font-family: Arial, sans-serif;
                    color: #2e2e38;
                    line-height: 1.6;
                    font-size: 11pt;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .ey-logo {
                    font-size: 48pt;
                    font-weight: bold;
                    color: #2e2e38;
                    background: #ffe600;
                    display: inline-block;
                    padding: 10px 25px;
                    border-radius: 8px;
                }
                h1 {
                    color: #2e2e38;
                    font-size: 24pt;
                    margin-top: 15px;
                }
                .ai-badge {
                    background: #e8f4fd;
                    border: 2px solid #0066cc;
                    color: #0066cc;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-size: 10pt;
                    display: inline-block;
                    margin-top: 10px;
                    font-weight: bold;
                }
                .status-box {
                    background: {{ status_color }};
                    border: 3px solid {{ status_border }};
                    padding: 25px;
                    margin: 25px 0;
                    border-radius: 8px;
                    text-align: center;
                }
                .status-icon {
                    font-size: 48pt;
                    margin-bottom: 10px;
                }
                .status-label {
                    font-size: 18pt;
                    font-weight: bold;
                    color: {{ status_text_color }};
                    margin-bottom: 10px;
                }
                .status-message {
                    font-size: 12pt;
                    color: {{ status_text_color }};
                }
                .info-table {
                    width: 100%;
                    margin: 25px 0;
                    border-collapse: collapse;
                }
                .info-table tr {
                    border-bottom: 1px solid #e2e8f0;
                }
                .info-table td {
                    padding: 12px 15px;
                }
                .info-table td:first-child {
                    font-weight: bold;
                    color: #64748b;
                    width: 40%;
                }
                .disclaimer {
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 25px 0;
                    font-size: 10pt;
                    color: #856404;
                }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    font-size: 9pt;
                    color: #94a3b8;
                    border-top: 1px solid #e2e8f0;
                    padding-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="ey-logo">EY</div>
                <h1>Payment Confirmation</h1>
                <div class="ai-badge">🤖 AI-Generated Document</div>
            </div>

            <div class="status-box">
                <div class="status-icon">{{ status_icon }}</div>
                <div class="status-label">{{ payment_status }}</div>
                <div class="status-message">{{ status_message }}</div>
            </div>

            <table class="info-table">
                <tr>
                    <td>Invoice Number:</td>
                    <td>{{ invoice_number }}</td>
                </tr>
                <tr>
                    <td>Invoice Amount:</td>
                    <td><strong>{{ amount }}</strong></td>
                </tr>
                <tr>
                    <td>Payment Status:</td>
                    <td><strong>{{ payment_status }}</strong></td>
                </tr>
                <tr>
                    <td>Due Date:</td>
                    <td>{{ due_date }}</td>
                </tr>
                {% if clearing_date != 'Not available' %}
                <tr>
                    <td>Clearing Date:</td>
                    <td>{{ clearing_date }}</td>
                </tr>
                {% endif %}
                <tr>
                    <td>Vendor/Customer:</td>
                    <td>{{ entity_name }}</td>
                </tr>
            </table>

            <div class="disclaimer">
                <strong>⚠️ Important Notice:</strong><br>
                This is an AI-generated payment confirmation based on available system data. 
                This is NOT an official payment receipt. For official payment confirmation, tax receipts, 
                or audit purposes, please contact your AP/AR team to request official documentation.
            </div>

            <div class="footer">
                Generated: {{ generated_at }}<br>
                EY Query Management System – AI Agent<br>
                Document created in response to ticket request
            </div>
        </body>
        </html>
        """

        template = Template(template_html)
        
        render_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_number": invoice_number,
            "amount": amount_display,
            "payment_status": payment_status,
            "status_color": status_color,
            "status_border": status_border,
            "status_text_color": status_text_color,
            "status_icon": status_icon,
            "status_message": status_message,
            "due_date": due_date,
            "clearing_date": clearing_date,
            "entity_name": entity_name,
        }

        html_content = template.render(**render_data)
        HTML(string=html_content).write_pdf(output_path)

        if os.path.exists(output_path):
            print(f"✓ AI-generated payment confirmation created: {output_path}")
            return output_path
        return None

    except Exception as e:
        print(f"✗ Payment confirmation generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def generate_invoice_details_pdf(invoice_data: dict, ticket_description: str = "", output_dir: str = "temp_docs") -> str | None:
    """
    Generate AI-generated invoice details document.
    Comprehensive view with all available information.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        inv_num = str(invoice_data.get("Invoice Number", "UNKNOWN")).replace("/", "-")
        output_filename = f"Invoice_Details_{inv_num}_{timestamp}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        # Extract all available data
        data_available = {}
        data_labels = {
            "Invoice Number": "Invoice Number",
            "Invoice Date": "Invoice Date",
            "Invoice Amount": "Invoice Amount",
            "Vendor Name": "Vendor Name",
            "Vendor ID": "Vendor ID",
            "Customer Name": "Customer Name",
            "Customer ID": "Customer ID",
            "Payment Status": "Payment Status",
            "Due Date": "Due Date",
            "Clearing Date": "Clearing Date",
            "PO Number": "PO Number",
            "PO Status": "PO Status",
            "Payment Term": "Payment Term",
            "Country": "Country",
        }
        
        for key, label in data_labels.items():
            value = invoice_data.get(key)
            if value and str(value).lower() not in ['nan', 'none', 'nat', '']:
                if 'Date' in key:
                    data_available[label] = str(value)[:10] if value else "N/A"
                elif key == "Invoice Amount":
                    try:
                        data_available[label] = f"${float(value):,.2f}"
                    except:
                        data_available[label] = str(value)
                else:
                    data_available[label] = str(value)

        invoice_number = invoice_data.get("Invoice Number", "N/A")

        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice Details</title>
            <style>
                @page { size: A4; margin: 2cm; }
                body {
                    font-family: Arial, sans-serif;
                    color: #2e2e38;
                    line-height: 1.6;
                    font-size: 11pt;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #ffe600;
                    padding-bottom: 20px;
                }
                .ey-logo {
                    font-size: 48pt;
                    font-weight: bold;
                    color: #2e2e38;
                    background: #ffe600;
                    display: inline-block;
                    padding: 10px 25px;
                    border-radius: 8px;
                }
                h1 {
                    color: #2e2e38;
                    font-size: 24pt;
                    margin-top: 15px;
                }
                .ai-badge {
                    background: #e8f4fd;
                    border: 2px solid #0066cc;
                    color: #0066cc;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-size: 10pt;
                    display: inline-block;
                    margin-top: 10px;
                    font-weight: bold;
                }
                .details-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 25px 0;
                    background: white;
                }
                .details-table th,
                .details-table td {
                    border: 1px solid #e2e8f0;
                    padding: 12px 15px;
                    text-align: left;
                }
                .details-table th {
                    background-color: #f8fafc;
                    font-weight: bold;
                    width: 35%;
                    color: #64748b;
                }
                .details-table td {
                    background-color: white;
                }
                .highlight-row td {
                    background-color: #fff7cc !important;
                    font-weight: bold;
                }
                .disclaimer {
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 25px 0;
                    font-size: 10pt;
                    color: #856404;
                }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    font-size: 9pt;
                    color: #94a3b8;
                    border-top: 1px solid #e2e8f0;
                    padding-top: 15px;
                }
                .generated-info {
                    text-align: right;
                    font-size: 9pt;
                    color: #64748b;
                    font-style: italic;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="ey-logo">EY</div>
                <h1>Invoice Details</h1>
                <div class="ai-badge">🤖 AI-Generated Document</div>
            </div>

            <div class="generated-info">
                Generated: {{ generated_at }}<br>
                Reference: {{ invoice_number }}
            </div>

            <table class="details-table">
                {% for label, value in data_items %}
                <tr {% if label == 'Invoice Number' or label == 'Invoice Amount' %}class="highlight-row"{% endif %}>
                    <th>{{ label }}</th>
                    <td>{{ value }}</td>
                </tr>
                {% endfor %}
            </table>

            <div class="disclaimer">
                <strong>⚠️ Important Notice:</strong><br>
                This is an AI-generated information document based on available system data. 
                While we strive for accuracy, this is NOT official documentation and should not be used 
                for legal, tax, or audit purposes. For official records, please contact your AP/AR team 
                to request authenticated documents.
            </div>

            <div class="footer">
                EY Query Management System – AI Agent<br>
                Automatically generated for: {{ ticket_description }}<br>
                For official documentation or verification, please contact your assigned team.
            </div>
        </body>
        </html>
        """

        template = Template(template_html)
        
        render_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "invoice_number": invoice_number,
            "data_items": list(data_available.items()),
            "ticket_description": ticket_description[:80] if ticket_description else "Invoice details request"
        }

        html_content = template.render(**render_data)
        HTML(string=html_content).write_pdf(output_path)

        if os.path.exists(output_path):
            print(f"✓ AI-generated invoice details created: {output_path}")
            return output_path
        return None

    except Exception as e:
        print(f"✗ Invoice details generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# Quick test
if __name__ == "__main__":
    print("Testing AI-Generated Document Generators...")
    print("=" * 60)
    
    # Test with minimal data (realistic scenario)
    minimal_invoice = {
        "Invoice Number": "INV-1001",
        "Invoice Amount": 1500.00,
        "Payment Status": "Paid",
    }
    
    # Test with more complete data
    complete_invoice = {
        "Invoice Number": "INV-2002",
        "Invoice Date": "2025-01-15",
        "Invoice Amount": 2500.50,
        "Vendor Name": "ABC Supplies",
        "Payment Status": "Unpaid",
        "Due Date": "2025-02-14",
        "PO Number": "PO-5001",
    }
    
    print("\n1. Testing with minimal data...")
    pdf1 = generate_invoice_copy_pdf(minimal_invoice, "Send invoice copy")
    print(f"   Result: {'SUCCESS' if pdf1 else 'FAILED'}")
    
    print("\n2. Testing payment confirmation...")
    pdf2 = generate_payment_confirmation_pdf(complete_invoice, "Payment status inquiry")
    print(f"   Result: {'SUCCESS' if pdf2 else 'FAILED'}")
    
    print("\n3. Testing invoice details...")
    pdf3 = generate_invoice_details_pdf(complete_invoice, "Invoice details request")
    print(f"   Result: {'SUCCESS' if pdf3 else 'FAILED'}")
    
    print("\n" + "=" * 60)
    print("✓ All tests complete!")