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
    for field in ["Submitter Email", "Requester Email", "Email"]:
        if field in ticket and ticket[field]:
            return str(ticket[field]).strip()

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
You are an EY Query Management AI Agent. Your goal is to analyze tickets and resolve or route them according to strict rules.

Follow EXACTLY these closure / handling categories — do NOT invent others:

1. "without_document"
   → Simple information requests — no document needed
   → Examples: payment status, invoice amount, due date, PO number, clearing date
   → Action: send informative email to requester → close ticket

2. "with_document"
   → User explicitly requests a document, copy, proof or remittance advice
   → Examples: "send invoice copy", "provide proof of payment", "remittance advice"
   → Action: send email to requester explaining that document generation is currently unavailable → close ticket

3. "needs_approval"
   → Actions with financial/risk/policy impact — requires manager sign-off
   → AP examples: validate vendor details, submit early payment request, put invoice on hold
   → AR examples: raise refund, investigate customer details, validate cancellation, block invoice
   → Action: set status "Pending Manager Approval" → send approval email to manager

4. "reassign_billing"
   → Billing-related specialist tickets — NOT resolved by AI
   → AP examples: raise reversal request, verify exchange rate
   → AR examples: credit memo creation, partial credit memo, debit memo creation
   → Action:
     - Do NOT close the ticket
     - Re-assign to correct team (AP or AR)
     - Send notification email to target team (manager email)
     - Send confirmation to original requester
     - Keep ticket Open / Assigned

First step: If ticket mentions invoice number, vendor, customer, PO etc. → ALWAYS call 'search_invoices' first.

Use professional EY-style language in all emails and responses.
Always explain your chosen handling type briefly in 'ai_response'.
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
                    "description": "Resolve the ticket using closure type 1,2,3.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {"type": "string"},
                            "ai_response": {"type": "string"},
                            "auto_solved": {"type": "boolean"},
                            "closure_type": {
                                "type": "string",
                                "enum": ["without_document", "with_document", "needs_approval"],
                            }
                        },
                        "required": ["ticket_id", "ai_response", "auto_solved", "closure_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reassign_ticket_and_notify",
                    "description": "Re-assign ticket to AP or AR team for billing specialist handling (category 4).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {"type": "string"},
                            "target_team": {"type": "string", "enum": ["AP", "AR"]},
                            "reason": {"type": "string"},
                            "ai_response": {"type": "string"}
                        },
                        "required": ["ticket_id", "target_team", "reason", "ai_response"]
                    }
                }
            }
        ]

    def process_ticket(self, ticket):
        ticket_id = str(ticket.get("Ticket ID"))
        description = str(ticket.get("Description", "No description provided."))
        status = str(ticket.get("Ticket Status", "Open")).lower()

        if status == "closed":
            print(f"Skipping Ticket {ticket_id}: Already Closed.")
            return "Ticket is already closed."

        print(f"\n--- Processing Ticket {ticket_id} ---")
        print(f"Description: {description[:120]}{'...' if len(description) > 120 else ''}")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Ticket ID: {ticket_id}\nDescription: {description}\nCurrent Team: {ticket.get('Assigned Team', 'Unknown')}"}
        ]

        max_turns = 6
        last_invoice_results = None

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
                    last_invoice_results = results
                    print(f"← Found {len(results)} record(s)")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": json.dumps(results, default=str)
                    })

                elif func_name == "resolve_ticket":
                    print(f"→ resolve_ticket called: {args}")
                    closure_type = args["closure_type"]
                    ai_response = args.get("ai_response", "Ticket processed by AI.")
                    auto_solved = args.get("auto_solved", True)

                    update_dict = {
                        "Auto Solved": auto_solved,
                        "AI Response": ai_response,
                        "Ticket Updated Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    email_subject = f"Update on Ticket {ticket_id}"
                    email_body = ai_response
                    recipient_email = None

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

The AI agent recommends closing Ticket {ticket_id}.

Team: {ticket.get('Assigned Team', 'N/A')}
Description: {description[:200]}

AI Resolution:
{ai_response}

Please review:
→ APPROVE: {approve_link}
→ REJECT & REOPEN: {reject_link}

Regards,
EY Query Management System
"""
                            send_email(
                                to_email=manager["email"],
                                subject=f"Approval Required: Ticket {ticket_id}",
                                body=email_body
                            )

                    else:
                        update_dict["Ticket Status"] = "Closed"
                        recipient_email = get_submitter_email(ticket)

                        if closure_type == "with_document":
                            email_body += "\n\n[Important Notice]\n"
                            email_body += "Invoice/document copy generation is currently unavailable.\n"
                            email_body += "Please contact your AP/AR team directly for a manual copy or further assistance.\n"
                            email_body += "We apologize for the inconvenience and are working to restore this feature."

                    success = update_multiple_fields(ticket_id, update_dict)

                    if success and recipient_email and closure_type != "needs_approval":
                        send_email(
                            to_email=recipient_email,
                            subject=email_subject,
                            body=email_body
                        )

                    if success:
                        print(f"✓ Ticket {ticket_id} → {closure_type}")
                    else:
                        print(f"✗ Update failed for {ticket_id}")

                    return f"Ticket {ticket_id} processed: {closure_type} | {ai_response}"

                elif func_name == "reassign_ticket_and_notify":
                    print(f"→ reassign_ticket_and_notify: {args}")
                    target_team = args["target_team"].upper()
                    reason = args.get("reason", "Billing specialist handling required")
                    ai_response = args.get("ai_response", f"Reassigned to {target_team} team.")

                    update_dict = {
                        "Assigned Team": target_team,
                        "Ticket Status": "Open",
                        "Ticket Updated Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "AI Response": ai_response,
                        "Auto Solved": False
                    }
                    update_dict["User Name"] = None  # clear assigned person

                    success = update_multiple_fields(ticket_id, update_dict)

                    if success:
                        # Email to requester
                        requester_email = get_submitter_email(ticket)
                        if requester_email:
                            send_email(
                                to_email=requester_email,
                                subject=f"Ticket {ticket_id} - Reassigned for Specialist Review",
                                body=f"""Dear Requester,

Your ticket {ticket_id} has been reviewed.

Reason: {reason}

Action: Reassigned to the {target_team} team for specialist processing.

You will be updated when actioned.

Regards,
EY Query Management System"""
                            )

                        # Email to target team (manager email)
                        team_manager = get_manager_by_team(target_team)
                        if team_manager:
                            send_email(
                                to_email=team_manager["email"],
                                subject=f"New Ticket Assigned: {ticket_id} ({target_team})",
                                body=f"""Hello {team_manager['name']},

Ticket {ticket_id} has been reassigned to {target_team}.

Original description: {description[:300]}

Reason: {reason}

Please review and process.

Regards,
EY Query Management AI Agent"""
                            )

                        print(f"✓ Ticket {ticket_id} reassigned → {target_team}")
                        return f"Ticket {ticket_id} reassigned to {target_team} | {ai_response}"
                    else:
                        return "Failed to reassign ticket."

        return "Agent reached maximum turns without resolving."

    def run_on_all_open_tickets(self):
        df = get_all_tickets_df()
        open_tickets = df[df["Ticket Status"].str.lower() != "closed"]

        results = []
        for _, row in open_tickets.iterrows():
            res = self.process_ticket(row.to_dict())
            results.append(res)
        return results


if __name__ == "__main__":
    print("Running TicketAIAgent on all open tickets...")
    agent = TicketAIAgent()
    agent.run_on_all_open_tickets()