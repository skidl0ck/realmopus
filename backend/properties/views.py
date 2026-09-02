import csv
import io

import django_filters
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, filters, generics, serializers as drf_serializers, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import ReadOnlyOrIsStaff, IsAdminOrSalesAgent, IsClient
from .models import Project, Lot, Reservation
from .serializers import ProjectSerializer, LotSerializer, ReservationSerializer, SelfServiceReservationSerializer

LOT_CSV_REQUIRED_COLUMNS = {"project", "block_number", "lot_number", "area_sqm", "price_per_sqm"}
LOT_CSV_OPTIONAL_COLUMNS = {"total_price", "status"}


class LotFilter(django_filters.FilterSet):
    """Adds range filtering (price, lot size) on top of the exact-match
    project/status filters -- plain filterset_fields only supports exact
    matches, not >=/<= ranges, so this needs its own FilterSet."""
    price_min = django_filters.NumberFilter(field_name="total_price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="total_price", lookup_expr="lte")
    area_min = django_filters.NumberFilter(field_name="area_sqm", lookup_expr="gte")
    area_max = django_filters.NumberFilter(field_name="area_sqm", lookup_expr="lte")

    class Meta:
        model = Lot
        fields = ["project", "status", "price_min", "price_max", "area_min", "area_max"]


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [ReadOnlyOrIsStaff]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "location"]

    def get_queryset(self):
        qs = Project.objects.all()
        user = self.request.user
        # Anonymous / client-facing browsing only sees published projects
        if not user.is_authenticated or user.role not in ("admin", "sales_agent", "accountant"):
            qs = qs.filter(is_published=True)
        return qs


class LotViewSet(viewsets.ModelViewSet):
    serializer_class = LotSerializer
    permission_classes = [ReadOnlyOrIsStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LotFilter
    search_fields = ["lot_number", "block_number"]
    ordering_fields = ["total_price", "area_sqm", "created_at"]

    def get_queryset(self):
        qs = Lot.objects.select_related("project").all()
        user = self.request.user
        if not user.is_authenticated or user.role not in ("admin", "sales_agent", "accountant"):
            qs = qs.filter(project__is_published=True, status=Lot.Status.AVAILABLE)
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Count public/client detail views for the "trending lots" dashboard —
        # excludes staff browsing their own inventory so numbers reflect real interest.
        if not request.user.is_authenticated or request.user.role not in ("admin", "sales_agent", "accountant"):
            Lot.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
            instance.refresh_from_db(fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False, methods=["post"],
        parser_classes=[MultiPartParser], permission_classes=[IsAdminOrSalesAgent],
    )
    def bulk_upload(self, request):
        """
        Bulk-create Lots from a CSV file (field name: 'file').

        Required columns: project (slug or ID), block_number, lot_number,
        area_sqm, price_per_sqm.
        Optional columns: total_price (auto-computed from area x price/sqm if
        omitted), status (defaults to 'available').

        Valid rows are created; invalid rows are skipped and reported —
        one bad row doesn't block the rest of the file.
        """
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "No file uploaded. Attach a CSV under the 'file' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "Couldn't read the file as UTF-8 text. Please upload a plain CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(decoded))
        columns = {c.strip() for c in (reader.fieldnames or [])}
        missing = LOT_CSV_REQUIRED_COLUMNS - columns
        if missing:
            return Response(
                {
                    "detail": (
                        f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                        f"Required: {', '.join(sorted(LOT_CSV_REQUIRED_COLUMNS))}. "
                        f"Optional: {', '.join(sorted(LOT_CSV_OPTIONAL_COLUMNS))}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, errors = [], []
        for line_number, raw_row in enumerate(reader, start=2):  # header is row 1
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items()}
            try:
                project_ref = row.get("project", "")
                project = Project.objects.filter(slug=project_ref).first()
                if project is None:
                    try:
                        project = Project.objects.filter(id=project_ref).first()
                    except (ValueError, ValidationError):
                        project = None
                if project is None:
                    raise ValueError(f"Project '{project_ref}' not found (use its slug or ID).")

                data = {
                    "project": project.id,
                    "block_number": row.get("block_number", ""),
                    "lot_number": row.get("lot_number", ""),
                    "area_sqm": row.get("area_sqm"),
                    "price_per_sqm": row.get("price_per_sqm"),
                }
                if row.get("total_price"):
                    data["total_price"] = row["total_price"]
                if row.get("status"):
                    data["status"] = row["status"]

                serializer = LotSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                lot = serializer.save()
                created.append({
                    "row": line_number,
                    "lot": f"{project.name} — Blk {lot.block_number} Lot {lot.lot_number}",
                })
            except drf_serializers.ValidationError as exc:
                errors.append({"row": line_number, "errors": exc.detail})
            except (ValueError, KeyError) as exc:
                errors.append({"row": line_number, "errors": str(exc)})

        response_status = status.HTTP_201_CREATED if not errors else status.HTTP_207_MULTI_STATUS
        return Response(
            {
                "created_count": len(created),
                "error_count": len(errors),
                "created": created,
                "errors": errors,
            },
            status=response_status,
        )


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAdminOrSalesAgent]

    def get_queryset(self):
        user = self.request.user
        qs = Reservation.objects.select_related("lot", "client", "agent").all()
        if user.is_sales_agent and not user.is_admin:
            qs = qs.filter(agent=user)
        return qs

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=["status"])
        reservation.lot.status = Lot.Status.AVAILABLE
        reservation.lot.save(update_fields=["status"])
        return Response(ReservationSerializer(reservation).data)


class MyReservationsView(generics.ListCreateAPIView):
    """Logged-in client self-service: reserve a lot for themselves (POST),
    or see their own reservations (GET) -- the public-site equivalent of a
    staff member creating a reservation for a walk-in prospect, except the
    client is reserving for themself and doesn't need to type buyer info
    that's already on their own profile."""

    serializer_class = SelfServiceReservationSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return Reservation.objects.filter(client=self.request.user).select_related("lot", "lot__project").order_by("-created_at")