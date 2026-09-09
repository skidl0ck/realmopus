from rest_framework import serializers
from .models import Notification, Testimonial, Inquiry, Blog


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "message", "is_read", "related_object_id", "created_at"]
        read_only_fields = fields


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ["id", "name", "role", "quote", "photo"]
        read_only_fields = fields


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ["id", "title", "slug", "summary", "content", "thumbnail", "video_url", "is_featured", "published_at"]
        read_only_fields = fields


class InquirySerializer(serializers.ModelSerializer):
    """Public-facing, write-only in practice -- this serializer is only ever
    used by the create endpoint (core.views.InquiryCreateView), which is
    itself POST-only, so there's no matching read path that could let an
    anonymous submitter (or anyone else) list or retrieve other people's
    inquiries through this serializer."""

    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "message", "source", "related_lot"]