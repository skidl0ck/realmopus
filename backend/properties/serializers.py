from rest_framework import serializers
from .models import Project, Lot, Reservation


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


class LotSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    # Auto-computed from area_sqm * price_per_sqm when not explicitly supplied — see validate().
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)

    class Meta:
        model = Lot
        fields = [
            "id", "project", "project_name", "block_number", "lot_number",
            "area_sqm", "price_per_sqm", "total_price", "status",
            "floor_plan", "photos", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

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
            "id", "lot", "lot_display", "client", "agent", "reservation_fee",
            "expires_at", "status", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_lot(self, lot):
        if lot.status != Lot.Status.AVAILABLE and not self.instance:
            raise serializers.ValidationError("This lot is not available for reservation.")
        return lot

    def create(self, validated_data):
        reservation = super().create(validated_data)
        lot = reservation.lot
        lot.status = Lot.Status.RESERVED
        lot.save(update_fields=["status"])
        return reservation
