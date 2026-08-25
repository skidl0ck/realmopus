from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """A user's own notifications — never another user's, regardless of role."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def site_config(request):
    """Public, unauthenticated — the public site and client portal both need
    the current currency symbol before a user is ever logged in."""
    from admin_panel.models import PlatformSettings
    return Response({"currency_symbol": PlatformSettings.load().currency_symbol})


CHAT_RATE_LIMIT = 15       # messages
CHAT_RATE_WINDOW = 60      # seconds


def _chat_rate_limited(request) -> bool:
    """Simple per-IP throttle so an unauthenticated public endpoint calling a
    paid API can't be trivially abused. Uses Django's default cache — fine
    for a single-process deployment; a real production setup behind multiple
    workers would want a shared cache (Redis) for this to work correctly
    across processes."""
    from django.core.cache import cache
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown")).split(",")[0].strip()
    key = f"chat_rate:{ip}"
    count = cache.get(key, 0)
    if count >= CHAT_RATE_LIMIT:
        return True
    cache.set(key, count + 1, timeout=CHAT_RATE_WINDOW)
    return False


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def chat(request):
    """Public site AND client portal chatbot — Q&A only, grounded in live
    published listings and staff-managed Knowledge Base entries, plus (when
    the requester is an authenticated client) their own real contract data.
    See core/chat.py for the system prompt and Gemini call itself.

    Conversations are persisted for the admin panel's Conversations/Dashboard/
    Analytics views — identified by a client-generated session_id (the public
    chat is anonymous, there's no logged-in user to key off of); portal chats
    additionally link the Conversation to the authenticated user.

    Security note: client_user is taken ONLY from request.user (the
    authenticated JWT identity) — never from anything in the request body —
    so there is no way for a request to ground itself in someone else's
    account data."""
    from .chat import get_chat_reply, ChatNotConfigured
    from .models import Conversation, ChatMessage
    from django.utils import timezone
    from accounts.models import User

    if _chat_rate_limited(request):
        return Response({"error": "Too many messages — please wait a moment and try again."}, status=429)

    messages = request.data.get("messages")
    if not isinstance(messages, list) or not messages:
        return Response({"error": "messages is required."}, status=400)

    session_id = str(request.data.get("session_id", "")).strip()
    if not session_id:
        return Response({"error": "session_id is required."}, status=400)

    client_user = request.user if (request.user.is_authenticated and request.user.role == User.Role.CLIENT) else None

    # The client resends the full history each turn (the chat itself is
    # stateless) — only the last message is actually new; everything before
    # it should already be persisted from prior turns.
    new_user_message = messages[-1]
    conversation = None
    if new_user_message.get("role") == "user" and new_user_message.get("content"):
        conversation, _ = Conversation.objects.get_or_create(session_id=session_id)
        if client_user and conversation.client_id != client_user.id:
            conversation.client = client_user
            conversation.save(update_fields=["client"])
        ChatMessage.objects.create(
            conversation=conversation, role=ChatMessage.Role.USER, content=new_user_message["content"][:2000],
        )
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])

    try:
        reply = get_chat_reply(messages, client_user=client_user)
    except ChatNotConfigured:
        return Response({"error": "The chat assistant isn't configured yet — please contact us directly."}, status=503)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Chat request failed")
        return Response({"error": "Something went wrong — please try again."}, status=502)

    if conversation:
        ChatMessage.objects.create(conversation=conversation, role=ChatMessage.Role.ASSISTANT, content=reply[:2000])
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])

    return Response({"reply": reply})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def chat_history(request):
    """Lets the widget restore a conversation after a page refresh, given the
    session_id it kept in localStorage. Public/anonymous chats are readable
    by session_id alone, same as before — it's an opaque, unguessable UUID.
    But once a conversation is linked to a client account (a portal chat,
    which may reference that buyer's real balance/schedule), it's only
    readable by that same authenticated client, not by session_id alone —
    a leaked/guessed session_id shouldn't be enough to read someone's
    account-grounded chat history."""
    from .models import Conversation

    session_id = request.GET.get("session_id", "").strip()
    if not session_id:
        return Response({"messages": []})
    conversation = Conversation.objects.filter(session_id=session_id).prefetch_related("chat_messages").first()
    if not conversation:
        return Response({"messages": []})
    if conversation.client_id and (not request.user.is_authenticated or request.user.id != conversation.client_id):
        return Response({"messages": []})
    return Response({
        "messages": [{"role": m.role, "content": m.content} for m in conversation.chat_messages.all()]
    })