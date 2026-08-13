from django import forms
from properties.models import Project, Lot

INPUT_CLASSES = "eo-input"


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "slug", "location", "description", "is_published"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "slug": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "location": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3}),
            "is_published": forms.CheckboxInput(attrs={"class": "eo-checkbox"}),
        }


class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = ["project", "block_number", "lot_number", "area_sqm", "price_per_sqm", "total_price", "status"]
        widgets = {
            "project": forms.Select(attrs={"class": INPUT_CLASSES}),
            "block_number": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "lot_number": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "area_sqm": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "price_per_sqm": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "total_price": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "status": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["total_price"].required = False

    def clean(self):
        cleaned = super().clean()
        area = cleaned.get("area_sqm")
        price_per_sqm = cleaned.get("price_per_sqm")
        if area is not None and price_per_sqm is not None and not cleaned.get("total_price"):
            cleaned["total_price"] = area * price_per_sqm
        return cleaned


class LotCSVUploadForm(forms.Form):
    file = forms.FileField(
        label="Lots CSV",
        widget=forms.ClearableFileInput(attrs={"class": "text-sm"}),
    )


# --- Sales: Contracts & Fees --------------------------------------------------
from sales.models import Contract, Fee


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "lot", "buyer_full_name", "buyer_email", "buyer_phone", "agent",
            "payment_plan_type", "total_contract_price", "down_payment", "term_months",
            "interest_rate", "penalty_rate_percent", "contract_date",
        ]
        widgets = {
            "lot": forms.Select(attrs={"class": INPUT_CLASSES}),
            "buyer_full_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "buyer_email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
            "buyer_phone": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "agent": forms.Select(attrs={"class": INPUT_CLASSES}),
            "payment_plan_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "total_contract_price": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "down_payment": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "term_months": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
            "interest_rate": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "penalty_rate_percent": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "contract_date": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from properties.models import Lot
        from accounts.models import User
        # Only lots not already tied to a contract can be sold
        self.fields["lot"].queryset = Lot.objects.filter(contract__isnull=True).order_by("project__name", "block_number")
        self.fields["agent"].queryset = User.objects.filter(role=User.Role.SALES_AGENT)
        self.fields["agent"].required = False

    def clean(self):
        cleaned = super().clean()
        plan_type = cleaned.get("payment_plan_type")
        term_months = cleaned.get("term_months")
        if plan_type == Contract.PaymentPlanType.INSTALLMENT and not term_months:
            self.add_error("term_months", "Required for installment payment plans.")
        down_payment = cleaned.get("down_payment")
        total_price = cleaned.get("total_contract_price")
        if down_payment is not None and total_price is not None and down_payment > total_price:
            self.add_error("down_payment", "Cannot exceed the total contract price.")
        return cleaned


class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ["name", "fee_type", "amount"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "fee_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
        }


# --- Payments ------------------------------------------------------------------
from payments.models import Payment


class ManualPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["contract", "installment", "amount", "method"]
        widgets = {
            "contract": forms.Select(attrs={"class": INPUT_CLASSES}),
            "installment": forms.Select(attrs={"class": INPUT_CLASSES}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "method": forms.Select(attrs={"class": INPUT_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from sales.models import Installment
        self.fields["method"].choices = [
            (Payment.Method.CASH, "Cash"),
            (Payment.Method.BANK_DEPOSIT, "Bank Deposit"),
            (Payment.Method.CHEQUE, "Cheque"),
        ]
        self.fields["installment"].queryset = Installment.objects.exclude(status="paid").select_related("contract")
        self.fields["installment"].required = False

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned = super().clean()
        installment = cleaned.get("installment")
        contract = cleaned.get("contract")
        if installment and contract and installment.contract_id != contract.id:
            self.add_error("installment", "This installment does not belong to the selected contract.")
        return cleaned


# --- Expenses --------------------------------------------------------------------
from expenses.models import Expense, ExpenseCategory


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["scope", "project", "category", "description", "amount", "incurred_on"]
        widgets = {
            "scope": forms.Select(attrs={"class": INPUT_CLASSES}),
            "project": forms.Select(attrs={"class": INPUT_CLASSES}),
            "category": forms.Select(attrs={"class": INPUT_CLASSES}),
            "description": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "incurred_on": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get("scope")
        project = cleaned.get("project")
        if scope == Expense.Scope.PROJECT and not project:
            self.add_error("project", "Required for project-specific expenses.")
        if scope == Expense.Scope.COMPANY and project:
            self.add_error("project", "Company-wide expenses shouldn't be tied to a project.")
        return cleaned


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": INPUT_CLASSES})}
