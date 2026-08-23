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

        # Pre-fill new contracts with the platform's suggested rates — staff can still
        # override per contract. Only applies on create, not when editing an instance.
        # Note: instance.pk is NOT a reliable "is this new" check here — Contract's
        # UUID primary key has a Python-side default (uuid.uuid4), so even a brand
        # new, never-saved instance already has a non-None pk. Use _state.adding instead.
        if self.instance._state.adding:
            settings_row = PlatformSettings.load()
            self.initial["interest_rate"] = settings_row.default_interest_rate_percent
            self.initial["penalty_rate_percent"] = settings_row.default_penalty_rate_percent

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


class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = [
            "currency_symbol",
            "default_penalty_rate_percent", "default_interest_rate_percent",
            "default_reservation_fee", "reservation_hold_days",
        ]
        widgets = {
            "currency_symbol": forms.TextInput(attrs={"class": INPUT_CLASSES, "maxlength": 5, "style": "max-width: 6rem;"}),
            "default_penalty_rate_percent": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "default_interest_rate_percent": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "default_reservation_fee": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
            "reservation_hold_days": forms.NumberInput(attrs={"class": INPUT_CLASSES}),
        }
        help_texts = {
            "currency_symbol": "Shown everywhere money is displayed — site-wide, and on all PDFs. Display only; amounts are never converted.",
            "default_penalty_rate_percent": "Suggested late-payment penalty rate for new installment contracts (staff can still override per contract).",
            "default_interest_rate_percent": "Suggested annual interest rate for new installment contracts (staff can still override per contract).",
            "default_reservation_fee": "Used by the public 'Reserve this lot' flow when no fee is specified.",
            "reservation_hold_days": "How many days a public reservation holds a lot before its deadline, when auto-created.",
        }


# --- Staff Users (Admin / Sales Agent / Accountant) & Commissions -----------------
from accounts.models import User, SalesAgentProfile
from django.contrib.auth.password_validation import validate_password as _validate_password

STAFF_ROLE_CHOICES = [
    (User.Role.ADMIN, "Admin"),
    (User.Role.SALES_AGENT, "Sales Agent"),
    (User.Role.ACCOUNTANT, "Accountant"),
]


class StaffCreateForm(forms.Form):
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, widget=forms.Select(attrs={"class": INPUT_CLASSES, "id": "id_role"}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT_CLASSES}))
    phone_number = forms.CharField(max_length=32, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}))
    # Only required/used when role == sales_agent — see clean().
    commission_type = forms.ChoiceField(
        choices=SalesAgentProfile.CommissionType.choices, required=False, widget=forms.Select(attrs={"class": INPUT_CLASSES})
    )
    commission_rate = forms.DecimalField(
        max_digits=8, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"}),
        help_text="Sales agents only — percentage (e.g. 3.00 for 3%) or a flat amount, depending on the type.",
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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.SALES_AGENT:
            if cleaned.get("commission_type") in (None, ""):
                self.add_error("commission_type", "Required for sales agents.")
            if cleaned.get("commission_rate") is None:
                self.add_error("commission_rate", "Required for sales agents.")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            phone_number=self.cleaned_data["phone_number"],
            password=self.cleaned_data["password"],
            role=self.cleaned_data["role"],
        )
        if user.role == User.Role.SALES_AGENT:
            SalesAgentProfile.objects.create(
                user=user,
                commission_type=self.cleaned_data["commission_type"],
                commission_rate=self.cleaned_data["commission_rate"],
            )
        return user


class StaffEditForm(forms.Form):
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, widget=forms.Select(attrs={"class": INPUT_CLASSES, "id": "id_role"}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT_CLASSES}))
    phone_number = forms.CharField(max_length=32, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASSES}))
    account_active = forms.BooleanField(required=False, label="Account active (can log in)")
    new_password = forms.CharField(
        required=False, widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}),
        help_text="Leave blank to keep their current password.",
    )
    # Only required when role == sales_agent (whether they already were one, or are
    # being switched to one now) — see clean()/save(). Pre-filled from any existing
    # agent profile even if their current role isn't sales_agent, so switching someone
    # back to Agent later restores their previous commission settings.
    commission_type = forms.ChoiceField(
        choices=SalesAgentProfile.CommissionType.choices, required=False, widget=forms.Select(attrs={"class": INPUT_CLASSES})
    )
    commission_rate = forms.DecimalField(
        max_digits=8, decimal_places=2, required=False, widget=forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01"})
    )
    profile_active = forms.BooleanField(required=False, label="Eligible for new commissions")

    def __init__(self, *args, user=None, editor=None, **kwargs):
        self.user = user
        self.editor = editor
        self.is_self_edit = bool(user and editor and user.pk == editor.pk)
        initial = kwargs.pop("initial", {})
        if user is not None:
            initial.update({
                "role": user.role,
                "first_name": user.first_name, "last_name": user.last_name,
                "email": user.email, "phone_number": user.phone_number,
                "account_active": user.is_active,
            })
            agent_profile = getattr(user, "agent_profile", None)
            if agent_profile:
                initial.update({
                    "commission_type": agent_profile.commission_type,
                    "commission_rate": agent_profile.commission_rate,
                    "profile_active": agent_profile.is_active,
                })
            else:
                initial.setdefault("profile_active", True)
        super().__init__(*args, initial=initial, **kwargs)

        if self.is_self_edit:
            # Editing your own account: role stays fixed no matter what's submitted —
            # Django's disabled=True ignores POST data for this field entirely, so this
            # can't be bypassed by tampering with the form. Prevents an admin (especially
            # the only one) from ever locking themselves out through this form.
            self.fields["role"].disabled = True

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        if password:
            _validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.SALES_AGENT:
            if cleaned.get("commission_type") in (None, ""):
                self.add_error("commission_type", "Required for sales agents.")
            if cleaned.get("commission_rate") is None:
                self.add_error("commission_rate", "Required for sales agents.")
        return cleaned

    def save(self):
        user = self.user
        user.role = self.cleaned_data["role"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.is_active = self.cleaned_data["account_active"]
        update_fields = ["role", "first_name", "last_name", "email", "phone_number", "is_active"]

        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
            update_fields.append("password")

        user.save(update_fields=update_fields)

        if user.role == User.Role.SALES_AGENT:
            # get_or_create rather than assuming user.agent_profile exists — a user
            # being switched TO sales_agent for the first time (or returning to it
            # after a prior downgrade left the profile untouched) both land here safely.
            # defaults= is required here: commission_type/commission_rate are NOT NULL
            # with no model-level default, so a bare get_or_create(user=user) would try
            # to INSERT with only the user set and fail the NOT NULL constraint before
            # ever reaching the field assignments below.
            profile, created = SalesAgentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "commission_type": self.cleaned_data["commission_type"],
                    "commission_rate": self.cleaned_data["commission_rate"],
                    "is_active": self.cleaned_data["profile_active"],
                },
            )
            if not created:
                profile.commission_type = self.cleaned_data["commission_type"]
                profile.commission_rate = self.cleaned_data["commission_rate"]
                profile.is_active = self.cleaned_data["profile_active"]
                profile.save(update_fields=["commission_type", "commission_rate", "is_active"])
        # If role != sales_agent: their agent_profile (if any) is deliberately left
        # untouched — kept as historical record rather than deactivated, per design.

        return user