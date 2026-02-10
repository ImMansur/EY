# utils/document_generator.py
"""
Utility to generate PDF documents for auto-closure with document requests.
Uses WeasyPrint to convert styled HTML to PDF.
"""

import os
from datetime import datetime
from weasyprint import HTML
from jinja2 import Template


def generate_invoice_info_pdf(
    invoice_data: dict,
    output_filename: str = None,
    output_dir: str = "temp_docs"
) -> str | None:
    """
    Generate a professional-looking PDF document with invoice details.

    Args:
        invoice_data: Dictionary containing invoice information
                     (from search_invoices result)
        output_filename: Optional custom filename (auto-generated if None)
        output_dir: Directory to save the PDF (will be created if missing)

    Returns:
        str | None: Full path to generated PDF file, or None if failed
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Auto-generate filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            inv_num = invoice_data.get("Invoice Number", "UNKNOWN").replace("/", "-")
            output_filename = f"Invoice_Info_{inv_num}_{timestamp}.pdf"

        output_path = os.path.join(output_dir, output_filename)

        # Jinja2 HTML template with inline CSS (EY branding colors)
        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>EY Invoice Information</title>
            <style>
                @page { size: A4; margin: 2cm; }
                body {
                    font-family: Arial, Helvetica, sans-serif;
                    color: #2e2e38;
                    line-height: 1.5;
                    font-size: 11pt;
                }
                .container {
                    max-width: 100%;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .ey-logo {
                    font-size: 36pt;
                    font-weight: bold;
                    color: #2e2e38;
                    background: #ffe600;
                    display: inline-block;
                    padding: 8px 16px;
                    border-radius: 8px;
                    margin-bottom: 8px;
                }
                h1 {
                    color: #2e2e38;
                    font-size: 22pt;
                    margin: 0;
                }
                .subtitle {
                    color: #64748b;
                    font-size: 12pt;
                }
                .info-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 25px 0;
                }
                .info-table th, .info-table td {
                    border: 1px solid #e2e8f0;
                    padding: 12px 15px;
                    text-align: left;
                }
                .info-table th {
                    background-color: #f8fafc;
                    font-weight: bold;
                    width: 35%;
                }
                .highlight {
                    background-color: #fff7cc;
                    font-weight: bold;
                }
                .footer {
                    margin-top: 50px;
                    text-align: center;
                    font-size: 9pt;
                    color: #64748b;
                    border-top: 1px solid #e2e8f0;
                    padding-top: 15px;
                }
                .generated {
                    font-style: italic;
                    color: #94a3b8;
                    text-align: right;
                    font-size: 9pt;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="ey-logo">EY</div>
                    <h1>Invoice Information</h1>
                    <p class="subtitle">Query Management System – Automated Response</p>
                </div>

                <div class="generated">
                    Generated on: {{ generated_at }}
                </div>

                <table class="info-table">
                    <tr>
                        <th>Invoice Number</th>
                        <td class="highlight">{{ invoice_number or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <th>Invoice Date</th>
                        <td>{{ invoice_date or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <th>Invoice Amount</th>
                        <td>{{ amount or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <th>Vendor</th>
                        <td>{{ vendor_name or 'N/A' }} (ID: {{ vendor_id or 'N/A' }})</td>
                    </tr>
                    <tr>
                        <th>Customer</th>
                        <td>{{ customer_name or 'N/A' }} (ID: {{ customer_id or 'N/A' }})</td>
                    </tr>
                    <tr>
                        <th>Payment Status</th>
                        <td>{{ payment_status or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <th>Due Date</th>
                        <td>{{ due_date or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <th>Clearing Date</th>
                        <td>{{ clearing_date or 'N/A' }}</td>
                    </tr>
                    <tr>
                        <th>PO Number</th>
                        <td>{{ po_number or 'N/A' }}</td>
                    </tr>
                    {% if additional_info %}
                    <tr>
                        <th>Additional Notes</th>
                        <td>{{ additional_info }}</td>
                    </tr>
                    {% endif %}
                </table>

                <div class="footer">
                    This document was automatically generated by the EY Query Management AI Agent.<br>
                    For verification or further assistance, please contact your assigned team member.
                </div>
            </div>
        </body>
        </html>
        """

        template = Template(template_html)

        # Prepare data for template
        render_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "invoice_number": invoice_data.get("Invoice Number"),
            "invoice_date": invoice_data.get("Invoice Date"),
            "amount": f"${float(invoice_data.get('Invoice Amount', 0)):.2f}" if invoice_data.get("Invoice Amount") else "N/A",
            "vendor_name": invoice_data.get("Vendor Name"),
            "vendor_id": invoice_data.get("Vendor ID"),
            "customer_name": invoice_data.get("Customer Name"),
            "customer_id": invoice_data.get("Customer ID"),
            "payment_status": invoice_data.get("Payment Status"),
            "due_date": invoice_data.get("Due Date"),
            "clearing_date": invoice_data.get("Clearing Date"),
            "po_number": invoice_data.get("PO Number"),
            "additional_info": invoice_data.get("Additional Info") or None,  # optional
        }

        html_content = template.render(**render_data)

        # Generate PDF
        HTML(string=html_content).write_pdf(output_path)

        if os.path.exists(output_path):
            print(f"PDF generated successfully: {output_path}")
            return output_path
        else:
            print("PDF file was not created.")
            return None

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return None


# Quick test when run directly
if __name__ == "__main__":
    # Sample data (replace with real search_invoices result)
    sample_invoice = {
        "Invoice Number": "INV-2025-0789",
        "Invoice Date": "2025-01-15",
        "Invoice Amount": 12500.75,
        "Vendor Name": "Tech Supplies Ltd",
        "Vendor ID": "VEND-456",
        "Customer Name": "Global Corp",
        "Customer ID": "CUST-789",
        "Payment Status": "Paid",
        "Due Date": "2025-02-14",
        "Clearing Date": "2025-02-10",
        "PO Number": "PO-98765",
    }

    pdf_path = generate_invoice_info_pdf(sample_invoice)
    if pdf_path:
        print(f"Test PDF created at: {pdf_path}")
    else:
        print("Test PDF generation failed.")