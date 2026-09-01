"""
AI chatbot backend — public site (this phase) and client portal (a later
phase, which will extend the system prompt with the logged-in buyer's own
account data). Deliberately Q&A only for now: it answers using real,
live data, but never takes an action (reserve a lot, record a payment, etc.).

Uses Google's Gemini API (free tier) rather than a paid model, per an
explicit cost decision — see GEMINI_API_KEY in .env.example. Requires the
google-genai package (the current SDK; the older google-generativeai
package is deprecated).
"""
from google import genai
from google.genai import types
from django.conf import settings

MAX_HISTORY_MESSAGES = 20  # stateless — the client resends recent history each turn
MAX_MESSAGE_LENGTH = 2000

SYSTEM_PROMPT_TEMPLATE = """You are the helpful assistant on {company_name}'s website, a real estate \
company selling residential lots in the Philippines.

Answer questions about the company, the buying process, and the lots currently listed below. Be warm, \
concise, and factual — never invent a price, lot, or availability status that isn't in the data provided.

If something is asked that isn't covered by the FAQ, the listings, or the company details below, say \
plainly that you don't have that specific information — don't guess, blend in your own general knowledge \
about real estate, or improvise an answer that sounds plausible. Point them to the support email below \
or a staff member instead.

You can only answer questions and provide information. You cannot reserve a lot, record a payment, check \
someone's personal account, or make any change — if asked, say a staff member can help with that, and \
point to the contact details below.

Company details:
- Name: {company_name}
- Address: {company_address}
- Support email: {support_email}

Currently listed projects and available lots:
{listings_summary}

Frequently asked questions (use these when relevant — they're maintained by staff and take priority over \
your own general knowledge):
{knowledge_base_summary}
"""

PORTAL_ADDENDUM_TEMPLATE = """

You are currently speaking with a logged-in buyer, {buyer_name}. You may also answer questions about their \
own account using the real data below — but ONLY their own data, never any other buyer's. You still cannot \
take any action (make a payment, change their schedule, etc.) — for that, direct them to their client portal \
or a staff member.

{buyer_name}'s contracts:
{contracts_summary}
"""


def _build_knowledge_base_summary() -> str:
    from core.models import KnowledgeBaseEntry

    entries = KnowledgeBaseEntry.objects.filter(is_active=True).order_by("question")
    if not entries.exists():
        return "(No FAQ entries yet.)"
    return "\n".join(f"Q: {e.question}\nA: {e.answer}" for e in entries)


def _build_listings_summary() -> str:
    from properties.models import Project, Lot

    projects = Project.objects.filter(is_published=True).order_by("name")
    if not projects.exists():
        return "(No projects are currently published.)"

    lines = []
    for project in projects:
        available = project.lots.filter(status=Lot.Status.AVAILABLE)
        if not available.exists():
            lines.append(f"- {project.name} ({project.location}): no available lots right now.")
            continue
        prices = available.values_list("total_price", flat=True)
        lines.append(
            f"- {project.name} ({project.location}): {available.count()} lot(s) available, "
            f"priced {min(prices):,.0f}–{max(prices):,.0f}."
        )
    return "\n".join(lines)


def _build_system_prompt(client_user=None) -> str:
    from admin_panel.models import PlatformSettings
    settings_row = PlatformSettings.load()
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        company_name=settings_row.company_name,
        company_address=settings_row.company_address or "(not set)",
        support_email=settings_row.support_email or "(not set)",
        listings_summary=_build_listings_summary(),
        knowledge_base_summary=_build_knowledge_base_summary(),
    )
    if client_user is not None:
        prompt += PORTAL_ADDENDUM_TEMPLATE.format(
            buyer_name=client_user.get_full_name() or client_user.username,
            contracts_summary=_build_contracts_summary(client_user),
        )
    return prompt


def _build_contracts_summary(client_user) -> str:
    """Every contract this buyer has ever had — including completed ones —
    covering balance, next due installment, and a receipts summary. Only
    ever called with the currently-authenticated user, never looked up by
    an ID the model or a message could supply, so one buyer's chat can
    never be grounded in another buyer's data."""
    contracts = client_user.contracts.select_related("lot", "lot__project").order_by("-contract_date")
    if not contracts.exists():
        return "(No contracts yet.)"

    lines = []
    for c in contracts:
        next_installment = (
            c.installments.exclude(status="paid").order_by("installment_number").first()
        )
        next_due = (
            f"{next_installment.due_date} — {next_installment.amount_due - next_installment.amount_paid:,.2f} due"
            if next_installment else "fully paid, nothing due"
        )
        receipts = c.payments.filter(status="completed").count()
        lines.append(
            f"- Contract {c.contract_number} ({c.get_status_display()}): "
            f"{c.lot.project.name}, Blk {c.lot.block_number} Lot {c.lot.lot_number}. "
            f"Plan: {c.get_payment_plan_type_display()}. "
            f"Total price: {c.total_contract_price:,.2f}. "
            f"Total paid: {c.total_paid:,.2f}. "
            f"Outstanding balance: {c.outstanding_balance:,.2f}. "
            f"Next due: {next_due}. "
            f"Receipts on file: {receipts}."
        )
    return "\n".join(lines)


class ChatNotConfigured(Exception):
    pass


def get_chat_reply(messages: list[dict], client_user=None) -> str:
    """
    messages: [{"role": "user"|"assistant", "content": "..."}], oldest first.
    client_user: the authenticated buyer, if this is a client-portal chat —
    None for the anonymous public-site chat.
    Returns the assistant's reply as plain text.
    """
    if not settings.GEMINI_API_KEY:
        raise ChatNotConfigured("GEMINI_API_KEY is not set in the environment.")

    trimmed = messages[-MAX_HISTORY_MESSAGES:]
    # Gemini uses "model" where Anthropic/OpenAI-style APIs use "assistant" —
    # translated here so the rest of the app (frontend, this module's callers)
    # can keep using the more common "assistant" convention.
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"][:MAX_MESSAGE_LENGTH])],
        )
        for m in trimmed if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_CHAT_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=_build_system_prompt(client_user),
            max_output_tokens=500,
        ),
    )
    return response.text or ""