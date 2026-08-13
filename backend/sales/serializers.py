from decimal import Decimal
from rest_framework import serializers
from .models import Contract, Fee, Installment, Commission


class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fee
        fields = ["id", "contract", "name", "fee_type", "amount"]
        read_only_fields = ["id"]


class InstallmentSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Installment
        fields = [
            "id", "contract", "installment_number", "due_date",
            "principal_amount", "fees_amount", "penalty_amount",
            "amount_due", "amount_paid", "balance", "status",
        ]
        read_only_fields = ["id", "amount_paid", "status"]


class CommissionSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.get_full_name", read_only=True)

    class Meta:
        model = Commission
        fields = ["id", "contract", "agent", "agent_name", "amount", "status", "released_at"]
        read_only_fields = ["id", "released_at"]


class ContractSerializer(serializers.ModelSerializer):
    fees = FeeSerializer(many=True, read_only=True)
    installments = InstallmentSerializer(many=True, read_only=True)
    commission = CommissionSerializer(read_only=True)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    financed_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    client_name = serializers.SerializerMethodField()
    lot_display = serializers.CharField(source="lot.__str__", read_only=True)
    is_claimed = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id", "contract_number", "lot", "lot_display",
            "buyer_full_name", "buyer_email", "buyer_phone",
            "client", "client_name", "is_claimed", "agent",
            "payment_plan_type", "total_contract_price", "down_payment", "term_months",
            "interest_rate", "penalty_rate_percent", "status", "contract_date", "contract_pdf",
            "fees", "installments", "commission",
            "financed_amount", "total_paid", "outstanding_balance",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "contract_number", "client", "created_at", "updated_at"]

    def get_client_name(self, obj):
        return obj.client.get_full_name() if obj.client else obj.buyer_full_name

    def get_is_claimed(self, obj):
        return obj.client_id is not None

    def validate(self, attrs):
        plan_type = attrs.get("payment_plan_type", getattr(self.instance, "payment_plan_type", None))
        term_months = attrs.get("term_months", getattr(self.instance, "term_months", 0))
        if plan_type == Contract.PaymentPlanType.INSTALLMENT and not term_months:
            raise serializers.ValidationError(
                {"term_months": "term_months is required for installment payment plans."}
            )
        down_payment = attrs.get("down_payment", getattr(self.instance, "down_payment", Decimal("0")))
        total_price = attrs.get("total_contract_price", getattr(self.instance, "total_contract_price", None))
        if total_price is not None and down_payment > total_price:
            raise serializers.ValidationError(
                {"down_payment": "Down payment cannot exceed the total contract price."}
            )
        return attrs


class ContractCreateSerializer(ContractSerializer):
    """Same as ContractSerializer but allows contract_number to be server-generated."""

    class Meta(ContractSerializer.Meta):
        pass

    def create(self, validated_data):
        if not validated_data.get("contract_number"):
            validated_data["contract_number"] = self._generate_contract_number()
        validated_data.setdefault("status", Contract.Status.ACTIVE)
        contract = Contract.objects.create(**validated_data)
        # Reflect the sale on the lot itself
        lot = contract.lot
        lot.status = lot.Status.SOLD
        lot.save(update_fields=["status"])
        return contract

    @staticmethod
    def _generate_contract_number():
        from django.utils import timezone
        year = timezone.now().year
        count = Contract.objects.filter(contract_number__startswith=f"GV-{year}-").count() + 1
        return f"GV-{year}-{count:04d}"