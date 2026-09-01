from rest_framework import serializers
from .models import Payment, Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    contract = serializers.SerializerMethodField()
    contract_number = serializers.SerializerMethodField()
    reservation = serializers.SerializerMethodField()
    lot_display = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = ["id", "payment", "contract", "contract_number", "reservation", "lot_display", "receipt_number", "pdf_file", "issued_at"]
        read_only_fields = ["id", "receipt_number", "issued_at"]

    def get_contract(self, obj):
        return str(obj.payment.contract_id) if obj.payment.contract_id else None

    def get_contract_number(self, obj):
        return obj.payment.contract.contract_number if obj.payment.contract_id else None

    def get_reservation(self, obj):
        return str(obj.payment.reservation_id) if obj.payment.reservation_id else None

    def get_lot_display(self, obj):
        lot = obj.payment.contract.lot if obj.payment.contract_id else obj.payment.reservation.lot
        if not lot:
            return None
        return f"{lot.project.name} — Blk {lot.block_number}, Lot {lot.lot_number}"


class PaymentSerializer(serializers.ModelSerializer):
    receipt = ReceiptSerializer(read_only=True)
    contract_number = serializers.SerializerMethodField()
    reservation_display = serializers.SerializerMethodField()
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "contract", "contract_number", "reservation", "reservation_display",
            "installment", "amount", "method",
            "status", "gateway_reference", "recorded_by", "recorded_by_name",
            "paid_at", "created_at", "receipt",
        ]
        read_only_fields = ["id", "status", "recorded_by", "paid_at", "created_at"]

    def get_contract_number(self, obj):
        return obj.contract.contract_number if obj.contract_id else None

    def get_reservation_display(self, obj):
        if not obj.reservation_id:
            return None
        r = obj.reservation
        return f"{r.buyer_full_name} — {r.lot}"

    def validate(self, attrs):
        installment = attrs.get("installment")
        contract = attrs.get("contract")
        reservation = attrs.get("reservation")
        if bool(contract) == bool(reservation):
            raise serializers.ValidationError(
                {"contract": "A payment must be linked to exactly one of a contract or a reservation."}
            )
        if installment and contract and installment.contract_id != contract.id:
            raise serializers.ValidationError(
                {"installment": "This installment does not belong to the selected contract."}
            )
        amount = attrs.get("amount")
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "Payment amount must be greater than zero."})
        return attrs


class ManualPaymentCreateSerializer(PaymentSerializer):
    """Used by staff recording cash/bank/cheque payments — completes immediately."""

    class Meta(PaymentSerializer.Meta):
        pass

    def validate_method(self, method):
        if method not in (Payment.Method.CASH, Payment.Method.BANK_DEPOSIT, Payment.Method.CHEQUE):
            raise serializers.ValidationError(
                "Use the gateway checkout endpoints for online payment methods."
            )
        return method