from rest_framework import serializers
from .models import Project, Lot, LotImage, Reservation


class ProjectSerializer(serializers.ModelSerializer):
    lot_count = serializers.SerializerMethodField()
    available_lot_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "name", "slug", "location", "description", "cover_image",
            "is_published", "lot_count", "available_lot_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_lot_count(self, obj):
        return obj.lots.count()

    def get_available_lot_count(self, obj):
        return obj.lots.filter(status=Lot.Status.AVAILABLE).count()


class LotImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotImage
        fields = ["id", "image", "is_thumbnail", "uploaded_at"]
        read_only_fields = fields


class LotSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    # Auto-computed from area_sqm * price_per_sqm when not explicitly supplied — see validate().
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    images = LotImageSerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Lot
        fields = [
            "id", "project", "project_name", "block_number", "lot_number",
            "area_sqm", "price_per_sqm", "total_price", "status", "view_count",
            "description", "floor_plan", "images", "thumbnail", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "view_count", "created_at", "updated_at"]

    def get_thumbnail(self, obj):
        thumb = obj.thumbnail
        if not thumb:
            return None
        request = self.context.get("request")
        url = thumb.image.url
        return request.build_absolute_uri(url) if request else url

    def validate(self, attrs):
        # keep total_price consistent when area/price-per-sqm are supplied without an explicit total
        area = attrs.get("area_sqm", getattr(self.instance, "area_sqm", None))
        price_per_sqm = attrs.get("price_per_sqm", getattr(self.instance, "price_per_sqm", None))
        if area is not None and price_per_sqm is not None and "total_price" not in attrs:
            attrs["total_price"] = area * price_per_sqm
        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    lot_display = serializers.CharField(source="lot.__str__", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "lot", "lot_display", "buyer_full_name", "buyer_email", "buyer_phone",
            "client", "agent", "reservation_fee", "deadline", "status", "created_at",
        ]
        read_only_fields = ["id", "client", "created_at"]

    def validate_lot(self, lot):
        if not self.instance:
            if lot.status != Lot.Status.AVAILABLE:
                raise serializers.ValidationError("This lot is not available for reservation.")
            if lot.reservations.filter(status__in=[Reservation.Status.ACTIVE, Reservation.Status.PENDING_PAYMENT]).exists():
                raise serializers.ValidationError("This lot already has an active reservation.")
        return lot

    def create(self, validated_data):
        reservation = super().create(validated_data)
        lot = reservation.lot
        lot.status = Lot.Status.RESERVED
        lot.save(update_fields=["status"])
        return reservation


class SelfServiceReservationSerializer(serializers.ModelSerializer):
    """A logged-in client reserving a lot for themselves on the public site.
    No separate buyer info to type in — pulled from their own profile —
    and follows the same pending-until-paid pattern as a staff-created
    reservation with a fee (see admin_panel/reservations_views.py:
    reservation_create): a fee > 0 means the lot goes on hold, not fully
    reserved, until that fee is actually paid."""

    lot_display = serializers.CharField(source="lot.__str__", read_only=True)

    class Meta:
        model = Reservation
        fields = ["id", "lot", "lot_display", "reservation_fee", "deadline", "status", "created_at"]
        read_only_fields = ["id", "reservation_fee", "deadline", "status", "created_at"]

    def validate_lot(self, lot):
        if lot.status != Lot.Status.AVAILABLE:
            raise serializers.ValidationError("This lot is not available for reservation.")
        if not lot.project.is_published:
            raise serializers.ValidationError("This lot is not currently open for reservations.")
        if lot.reservations.filter(status__in=[Reservation.Status.ACTIVE, Reservation.Status.PENDING_PAYMENT]).exists():
            raise serializers.ValidationError("This lot already has an active reservation.")
        return lot

    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta
        from admin_panel.models import PlatformSettings

        user = self.context["request"].user
        settings_row = PlatformSettings.load()
        fee = settings_row.default_reservation_fee or 0

        reservation = Reservation.objects.create(
            lot=validated_data["lot"],
            client=user,
            buyer_full_name=user.get_full_name() or user.username,
            buyer_email=user.email,
            buyer_phone=user.phone_number,
            reservation_fee=fee,
            deadline=timezone.now().date() + timedelta(days=settings_row.reservation_hold_days),
            status=Reservation.Status.PENDING_PAYMENT if fee > 0 else Reservation.Status.ACTIVE,
        )
        lot = reservation.lot
        lot.status = Lot.Status.ON_HOLD if fee > 0 else Lot.Status.RESERVED
        lot.save(update_fields=["status"])
        return reservation