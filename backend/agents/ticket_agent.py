# agents/ticket_agent.py
import hashlib
import os
import json
from datetime import datetime
from openai import AzureOpenAI
from utils import get_user_email_by_name, get_manager_by_team
from email_service import send_email
from config import get_azure_client, get_deployment_name
from table_db import get_all_tickets_df, search_invoices, update_multiple_fields

# ────────────────────────────────────────────────
# Approval Token Generator
# ────────────────────────────────────────────────
def generate_approval_token(ticket_id: str) -> str:
    secret = os.getenv("APPROVAL_SECRET", "ey_approval_secret")
    raw = f"{ticket_id}:{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_submitter_email(ticket: dict) -> str | None:
    """
    Attempt to find the best email to notify about ticket resolution.
    """
    # 1. Direct field if it exists
    for field in ["Submitter Email", "Requester Email", "Email"]:
        if field in ticket and ticket[field]:
            return str(ticket[field]).strip()

    # 2. Fallback to User Name → lookup in user.json
    user_name = ticket.get("User Name") or ticket.get("Assigned To")
    if user_name:
        email = get_user_email_by_name(user_name)
        if email:
            return email

    return None


class TicketAIAgent:
    def __init__(self):
        self.client = get_azure_client()
        self.deployment = get_deployment_name()
        self.system_prompt = """
        You are an EY Query Management AI Agent. Your goal is to analyze tickets and resolve them if possible.
        If a ticket involves an invoice (status check, payment query, PO info, copy request), use the 'search_invoices' tool first.

        Available Invoice Data:
        - Invoice Number, Invoice Date, Invoice Amount
        - Vendor ID, Vendor Name
        - PO Number, PO Status
        - Payment Status, Payment Term, Due Date, Clearing Date
        - Customer ID, Customer Name, Country

        === CLOSURE TYPES - VERY IMPORTANT ===

        When you have enough information to resolve the ticket, ALWAYS call 'resolve_ticket' and choose the correct closure_type:

        1. "without_document"
           → Use for simple status checks or information requests
           → Examples: "What is the payment status?", "When was invoice cleared?", "Show invoice details"
           → Result: Email sent to requester with answer → ticket closed immediately

        2. "with_document"
           → Use ONLY when the user explicitly asks for a document/copy/proof
           → Examples: "Send me invoice copy", "Please provide proof of payment", "Remittance advice"
           → Set attachment_filename if you know it (e.g. "invoice_{number}.pdf")
           → Result: Document generated + attached to email → ticket closed

        3. "needs_approval"
           → Use for actions requiring manager sign-off
           → AP examples: validate vendor details, submit early payment request, put invoice on hold
           → AR examples: raise refund, investigate customer details, validate cancellation, block invoice
           → Result: Ticket → "Pending Manager Approval" → approval email sent to manager

        Always explain your choice briefly in ai_response.
        Provide clear, professional language suitable for direct email to user or manager.
        """

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_invoices",
                    "description": "Search the invoice database for matching records.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "Invoice Number": {"type": "string"},
                            "Customer Name": {"type": "string"},
                            "Vendor Name": {"type": "string"},
                            "Payment Status": {"type": "string"},
                            "PO Number": {"type": "string"},
                            "Vendor ID": {"type": "string"},
                            "Customer ID": {"type": "string"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "resolve_ticket",
                    "description": "Resolve the ticket using the correct closure type.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {"type": "string"},
                            "ai_response": {"type": "string"},
                            "auto_solved": {"type": "boolean"},
                            "closure_type": {
                                "type": "string",
                                "enum": ["without_document", "with_document", "needs_approval"],
                                "description": "Required. Choose based on system prompt rules."
                            },
                            "attachment_filename": {
                                "type": ["string", "null"],
                                "description": "Only for with_document - suggested filename"
                            }
                        },
                        "required": ["ticket_id", "ai_response", "auto_solved", "closure_type"]
                    }
                }
            }
        ]

    def process_ticket(self, ticket):
        ticket_id = str(ticket.get("Ticket ID"))
        description = str(ticket.get("Description", "No description provided."))
        status = str(ticket.get("Ticket Status", "Open"))

        if status.lower() == "closed":
            print(f"Skipping Ticket {ticket_id}: Already Closed.")
            return "Ticket is already closed."

        print(f"\n--- Processing Ticket {ticket_id} ---")
        print(f"Description: {description[:120]}{'...' if len(description) > 120 else ''}")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Ticket ID: {ticket_id}\nDescription: {description}"}
        ]

        max_turns = 5
        for turn in range(max_turns):
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                tools=self.get_tool_definitions(),
                tool_choice="auto"
            )

            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                print(f"Final non-tool response: {msg.content}")
                return msg.content or "No resolution reached."

            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if func_name == "search_invoices":
                    print(f"→ Searching invoices: {args}")
                    results = search_invoices(args)
                    print(f"← Found {len(results)} record(s)")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": json.dumps(results, default=str)
                    })

                elif func_name == "resolve_ticket":
                    print(f"→ resolve_ticket called: {args}")

                    closure_type = args.get("closure_type", "without_document")
                    ai_response = args.get("ai_response", "Ticket processed by AI agent.")
                    auto_solved = args.get("auto_solved", True)
                    attachment = args.get("attachment_filename")

                    update_dict = {
                        "Auto Solved": auto_solved,
                        "AI Response": ai_response,
                    }

                    manager = None
                    recipient_email = None
                    email_subject = f"Update on Ticket {ticket_id}"
                    email_body = ai_response
                    attachment_path = None

                    if closure_type == "needs_approval":
                        update_dict["Ticket Status"] = "Pending Manager Approval"
                        update_dict["Admin Review Needed"] = "Yes"

                        manager = get_manager_by_team(ticket.get("Assigned Team"))
                        if manager:
                            token = generate_approval_token(ticket_id)
                            base_url = os.getenv("APP_BASE_URL", "http://localhost:5000")
                            approve_link = f"{base_url}/ticket/approve/{ticket_id}?token={token}"
                            reject_link = f"{base_url}/ticket/reject/{ticket_id}?token={token}"

                            email_body = f"""Hello {manager['name']},

The AI agent has resolved Ticket {ticket_id}.

Team: {ticket.get('Assigned Team', 'N/A')}

AI Resolution:
{ai_response}

Please review:
→ APPROVE: {approve_link}
→ REJECT & REOPEN: {reject_link}

Regards,
EY Query Management System
"""
                            send_email(
                                to_email=manager['email'],
                                subject=f"Approval Required: Ticket {ticket_id}",
                                body=email_body
                            )

                    else:
                        # Direct closure: without_document or with_document
                        update_dict["Ticket Status"] = "Closed"
                        recipient_email = get_submitter_email(ticket)

                        if closure_type == "with_document":
                            # ─────────────── GENERATED DOCUMENT LOGIC ───────────────
                            # This is where you plug in document_generator.py
                            # Example:
                            """
                            from utils.document_generator import generate_invoice_info_pdf

                            # Assume you have the invoice data from search
                            # (you may need to store last search result in agent state)
                            invoice_results = search_invoices({"Invoice Number": "YOUR_INVOICE_NUMBER_HERE"})
                            if invoice_results:
                                invoice_data = invoice_results[0]
                                temp_pdf = f"temp_doc_{ticket_id}.pdf"
                                pdf_path = generate_invoice_info_pdf(invoice_data, temp_pdf)
                                if pdf_path:
                                    attachment_path = pdf_path
                                else:
                                    email_body += "\n\n(Note: Document generation failed)"
                            else:
                                email_body += "\n\n(No invoice data available for document)"
                            """

                            # Placeholder until document generation is connected
                            email_body += "\n\n[Attachment would be included here if document was generated]"

                    # ─── Update Excel ───────────────────────────────────────
                    success = update_multiple_fields(ticket_id, update_dict)

                    # ─── Send resolution email when appropriate ────────────
                    if success and recipient_email and closure_type != "needs_approval":
                        send_email(
                            to_email=recipient_email,
                            subject=email_subject,
                            body=email_body,
                            attachment_path=attachment_path
                        )

                        # Optional: clean up temp file
                        if attachment_path and os.path.exists(attachment_path):
                            try:
                                os.remove(attachment_path)
                            except:
                                pass

                    if success:
                        print(f"✓ Ticket {ticket_id} updated → {closure_type}")
                    else:
                        print(f"✗ Failed to update ticket {ticket_id}")

                    return f"Ticket {ticket_id} processed: {closure_type} | {ai_response}"

        return "Agent reached maximum turns without resolving."

    def run_on_all_open_tickets(self):
        df = get_all_tickets_df()
        open_tickets = df[df["Ticket Status"] != "Closed"]

        results = []
        for _, row in open_tickets.iterrows():
            res = self.process_ticket(row.to_dict())
            results.append(res)
        return results


if __name__ == "__main__":
    print("Running TicketAIAgent on all open tickets...")
    agent = TicketAIAgent()
    agent.run_on_all_open_tickets()