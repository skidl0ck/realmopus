from rest_framework import serializers
from .models import Expense, ExpenseCategory


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name"]


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id", "scope", "project", "project_name", "category", "category_name",
            "description", "amount", "receipt_file", "recorded_by", "recorded_by_name",
            "incurred_on", "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "created_at"]

    def validate(self, attrs):
        scope = attrs.get("scope", getattr(self.instance, "scope", None))
        project = attrs.get("project", getattr(self.instance, "project", None))
        if scope == Expense.Scope.PROJECT and not project:
            raise serializers.ValidationError(
                {"project": "A project is required for project-specific expenses."}
            )
        if scope == Expense.Scope.COMPANY and project:
            raise serializers.ValidationError(
                {"project": "Company-wide expenses shouldn't be tied to a specific project."}
            )
        return attrs