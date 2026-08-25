import re
from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from core.models import Conversation, ChatMessage, KnowledgeBaseEntry

from .decorators import dynamic_permission, audit_action
from .forms import KnowledgeBaseEntryForm

# Common English words excluded from the "popular questions" keyword count —
# a deliberately simple frequency count, not real topic clustering/NLP.
STOPWORDS = {
    "the", "a", "an", "is", "are", "do", "does", "i", "you", "your", "my", "me",
    "what", "how", "can", "will", "for", "of", "to", "in", "on", "and", "or",
    "it", "this", "that", "have", "has", "with", "about", "there", "if", "be",
    "would", "could", "when", "where", "who", "any", "please", "thanks", "hi",
    "hello", "want", "need", "know", "get",
}


@dynamic_permission("chatbot", "view")
def chatbot_dashboard(request):
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)

    total_conversations = Conversation.objects.count()
    messages_today = ChatMessage.objects.filter(created_at__date=today).count()
    messages_this_week = ChatMessage.objects.filter(created_at__date__gte=week_ago).count()

    conversation_count = Conversation.objects.count()
    total_messages = ChatMessage.objects.count()
    avg_messages = round(total_messages / conversation_count, 1) if conversation_count else 0

    recent_conversations = (
        Conversation.objects.annotate(message_count=Count("chat_messages"))
        .order_by("-last_message_at")[:8]
    )

    return render(request, "admin_panel/chatbot/dashboard.html", {
        "total_conversations": total_conversations,
        "messages_today": messages_today,
        "messages_this_week": messages_this_week,
        "avg_messages": avg_messages,
        "recent_conversations": recent_conversations,
    })


@dynamic_permission("chatbot", "view")
def conversation_list(request):
    conversations = Conversation.objects.annotate(message_count=Count("chat_messages")).order_by("-last_message_at")

    search = request.GET.get("q", "").strip()
    if search:
        conversations = conversations.filter(chat_messages__content__icontains=search).distinct()

    return render(request, "admin_panel/chatbot/conversation_list.html", {
        "conversations": conversations,
        "search": search,
    })


@dynamic_permission("chatbot", "view")
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation.objects.prefetch_related("chat_messages"), pk=pk)
    return render(request, "admin_panel/chatbot/conversation_detail.html", {"conversation": conversation})


@dynamic_permission("chatbot", "view")
def chatbot_analytics(request):
    range_param = request.GET.get("range", "30d")
    days = {"7d": 7, "30d": 30, "90d": 90}.get(range_param, 30)
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)

    # Usage trend: messages per day
    daily_counts = (
        ChatMessage.objects.filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
    )
    counts_by_day = {row["day"]: row["count"] for row in daily_counts}
    chart_labels, chart_counts = [], []
    for i in range(days):
        d = start_date + timedelta(days=i)
        chart_labels.append(f"{d.strftime('%b')} {d.day}")
        chart_counts.append(counts_by_day.get(d, 0))

    # Busiest times: messages by hour of day
    hourly = (
        ChatMessage.objects.filter(created_at__date__gte=start_date)
        .annotate(hour=TruncHour("created_at"))
        .values("hour")
    )
    hour_counts = Counter()
    for row in hourly:
        hour_counts[row["hour"].hour] += 1
    hour_labels = [f"{h:02d}:00" for h in range(24)]
    hour_data = [hour_counts.get(h, 0) for h in range(24)]

    # Popular topics: simple keyword frequency from user messages (not real
    # NLP/clustering — a pragmatic approximation given the scope of this build)
    user_messages = ChatMessage.objects.filter(
        role=ChatMessage.Role.USER, created_at__date__gte=start_date
    ).values_list("content", flat=True)
    word_counts = Counter()
    for content in user_messages:
        words = re.findall(r"[a-zA-Z']{3,}", content.lower())
        word_counts.update(w for w in words if w not in STOPWORDS)
    top_keywords = word_counts.most_common(15)

    return render(request, "admin_panel/chatbot/analytics.html", {
        "range_param": range_param,
        "chart_labels": chart_labels,
        "chart_counts": chart_counts,
        "hour_labels": hour_labels,
        "hour_data": hour_data,
        "top_keywords": top_keywords,
        "total_messages_in_range": sum(chart_counts),
    })


@dynamic_permission("chatbot", "view")
def kb_list(request):
    entries = KnowledgeBaseEntry.objects.all()
    category = request.GET.get("category")
    if category:
        entries = entries.filter(category=category)
    return render(request, "admin_panel/chatbot/kb_list.html", {
        "entries": entries,
        "categories": KnowledgeBaseEntry.Category.choices,
        "selected_category": category or "",
    })


@dynamic_permission("chatbot", "edit")
@audit_action("created_kb_entry", model_name="KnowledgeBaseEntry", get_object_id=lambda request: None)
def kb_create(request):
    if request.method == "POST":
        form = KnowledgeBaseEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Knowledge base entry added.")
            return redirect("admin_panel:kb_list")
    else:
        form = KnowledgeBaseEntryForm()
    return render(request, "admin_panel/chatbot/kb_form.html", {"form": form, "title": "New FAQ Entry"})


@dynamic_permission("chatbot", "edit")
@audit_action("edited_kb_entry", model_name="KnowledgeBaseEntry", get_object_id=lambda request, pk: pk)
def kb_edit(request, pk):
    entry = get_object_or_404(KnowledgeBaseEntry, pk=pk)
    if request.method == "POST":
        form = KnowledgeBaseEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Knowledge base entry updated.")
            return redirect("admin_panel:kb_list")
    else:
        form = KnowledgeBaseEntryForm(instance=entry)
    return render(request, "admin_panel/chatbot/kb_form.html", {"form": form, "title": "Edit FAQ Entry"})


@dynamic_permission("chatbot", "edit")
@audit_action("deleted_kb_entry", model_name="KnowledgeBaseEntry", get_object_id=lambda request, pk: pk)
def kb_delete(request, pk):
    entry = get_object_or_404(KnowledgeBaseEntry, pk=pk)
    entry.delete()
    messages.success(request, "Knowledge base entry deleted.")
    return redirect("admin_panel:kb_list")