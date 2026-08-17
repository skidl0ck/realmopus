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
        fields = ["project", "block_number", "lot_number", "area_sqm", "price_per_sqm", "total_price", "status", "description"]
        widgets = {
            "project": forms.Select(attrs={"class": INPUT_CLASSES}),
            "block_number": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "lot_number": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "area_sqm": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "price_per_sqm": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "total_price": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "status": forms.Select(attrs={"class": INPUT_CLASSES}),
            "description": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["total_price"].required = False
        self.fields["description"].required = False

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
        # These fields are optional in the form (blank=True) but NOT NULL in the DB —
        # fall back to their model defaults rather than letting None reach save().
        if cleaned.get("term_months") is None:
            cleaned["term_months"] = 0
        if cleaned.get("interest_rate") is None:
            cleaned["interest_rate"] = Contract._meta.get_field("interest_rate").default
        if cleaned.get("penalty_rate_percent") is None:
            cleaned["penalty_rate_percent"] = Contract._meta.get_field("penalty_rate_percent").default
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


class ExpenseCSVUploadForm(forms.Form):
    file = forms.FileField(
        label="Expenses CSV",
        widget=forms.ClearableFileInput(attrs={"class": "text-sm"}),
    )


# --- Reservations ---------------------------------------------------------------
from properties.models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["lot", "buyer_full_name", "buyer_email", "buyer_phone", "agent", "reservation_fee", "deadline"]
        widgets = {
            "lot": forms.Select(attrs={"class": INPUT_CLASSES}),
            "buyer_full_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "buyer_email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
            "buyer_phone": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "agent": forms.Select(attrs={"class": INPUT_CLASSES}),
            "reservation_fee": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "deadline": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.db.models import Q
        from properties.models import Lot
        from accounts.models import User

        # A lot is reservable if it's currently available, OR it's the lot already
        # tied to this reservation being edited (so editing doesn't lose the option).
        lot_filter = Q(status=Lot.Status.AVAILABLE)
        if self.instance and self.instance.pk:
            lot_filter |= Q(pk=self.instance.lot_id)
        self.fields["lot"].queryset = Lot.objects.filter(lot_filter).select_related("project")

        self.fields["agent"].queryset = User.objects.filter(role=User.Role.SALES_AGENT)
        self.fields["agent"].required = False
        self.fields["reservation_fee"].required = False

    def clean_lot(self):
        lot = self.cleaned_data["lot"]
        if not self.instance.pk:
            if lot.reservations.filter(status=Reservation.Status.ACTIVE).exists():
                raise forms.ValidationError("This lot already has an active reservation.")
        return lot


# --- Document Settings ------------------------------------------------------------
from .models import PlatformSettings


class DocumentSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = ["company_name", "company_address", "company_logo", "support_email", "document_footer_note"]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "company_address": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "support_email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
            "document_footer_note": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company_address"].required = False
        self.fields["company_logo"].required = False
        self.fields["support_email"].required = False
        self.fields["document_footer_note"].required = False


# --- Agents & Commissions ---------------------------------------------------------
from accounts.models import User, SalesAgentProfile
from django.contrib.auth.password_validation import validate_password as _validate_password


class AgentCreateForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT_CLASSES}))
    phone_number = forms.CharField(max_length=32, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}))
    commission_type = forms.ChoiceField(
        choices=SalesAgentProfile.CommissionType.choices, widget=forms.Select(attrs={"class": INPUT_CLASSES})
    )
    commission_rate = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
        help_text="Percentage (e.g. 3.00 for 3%) or a flat amount, depending on the type selected above.",
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        _validate_password(password)
        return password

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            phone_number=self.cleaned_data["phone_number"],
            password=self.cleaned_data["password"],
            role=User.Role.SALES_AGENT,
        )
        SalesAgentProfile.objects.create(
            user=user,
            commission_type=self.cleaned_data["commission_type"],
            commission_rate=self.cleaned_data["commission_rate"],
        )
        return user


class AgentEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT_CLASSES}))
    phone_number = forms.CharField(max_length=32, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    account_active = forms.BooleanField(required=False, label="Account active (can log in)")
    commission_type = forms.ChoiceField(
        choices=SalesAgentProfile.CommissionType.choices, widget=forms.Select(attrs={"class": INPUT_CLASSES})
    )
    commission_rate = forms.DecimalField(
        max_digits=8, decimal_places=2, widget=forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"})
    )
    profile_active = forms.BooleanField(required=False, label="Eligible for new commissions")

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        initial = kwargs.pop("initial", {})
        if user is not None:
            initial.update({
                "first_name": user.first_name, "last_name": user.last_name,
                "email": user.email, "phone_number": user.phone_number,
                "account_active": user.is_active,
                "commission_type": user.agent_profile.commission_type,
                "commission_rate": user.agent_profile.commission_rate,
                "profile_active": user.agent_profile.is_active,
            })
        super().__init__(*args, initial=initial, **kwargs)

    def save(self):
        user = self.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.is_active = self.cleaned_data["account_active"]
        user.save(update_fields=["first_name", "last_name", "email", "phone_number", "is_active"])

        profile = user.agent_profile
        profile.commission_type = self.cleaned_data["commission_type"]
        profile.commission_rate = self.cleaned_data["commission_rate"]
        profile.is_active = self.cleaned_data["profile_active"]
        profile.save(update_fields=["commission_type", "commission_rate", "is_active"])
        return user