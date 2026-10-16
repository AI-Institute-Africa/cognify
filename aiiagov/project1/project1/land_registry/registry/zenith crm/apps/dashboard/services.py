from calendar import month_abbr
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from apps.customers.models import Customer
from apps.leads.models import Lead
from .models import Expense, RevenueStream


class DashboardService:
    @staticmethod
    def _get_monthly_range(months=6):
        today = timezone.localdate()
        labels = []
        month_ranges = []
        year = today.year
        month = today.month

        for offset in range(months - 1, -1, -1):
            current_month = month - offset
            current_year = year
            while current_month <= 0:
                current_month += 12
                current_year -= 1
            labels.append(f"{month_abbr[current_month]} {current_year}")
            month_ranges.append((current_year, current_month))

        return labels, month_ranges

    @staticmethod
    def get_chart_data(user, months=6):
        revenue_qs = RevenueStream.objects.filter(user=user)
        expense_qs = Expense.objects.filter(user=user)

        labels, month_ranges = DashboardService._get_monthly_range(months)
        revenue_series = []
        expense_series = []

        for year, month in month_ranges:
            revenue_series.append(
                revenue_qs.filter(date__year=year, date__month=month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            )
            expense_series.append(
                expense_qs.filter(date__year=year, date__month=month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            )

        revenue_breakdown = [
            {
                "label": display,
                "amount": revenue_qs.filter(stream_type=stream_type).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
            }
            for stream_type, display in RevenueStream.STREAM_CHOICES
        ]

        top_revenue_sources = sorted(
            [item for item in revenue_breakdown if item["amount"] > 0],
            key=lambda item: item["amount"],
            reverse=True,
        )[:4]

        expense_breakdown = [
            {
                "label": row["category"] or "General",
                "amount": row["total"],
            }
            for row in expense_qs.values("category").annotate(total=Sum("amount")).order_by("-total")[:5]
        ]

        return {
            "trend_labels": labels,
            "trend_revenue": revenue_series,
            "trend_expenses": expense_series,
            "revenue_breakdown": revenue_breakdown,
            "top_revenue_sources": top_revenue_sources,
            "expense_breakdown": expense_breakdown,
        }

    @staticmethod
    def get_metrics(user):
        today = timezone.localdate()
        customers_count = Customer.objects.count()
        leads_count = Lead.objects.count()

        revenue_qs = RevenueStream.objects.filter(user=user)
        expense_qs = Expense.objects.filter(user=user)
        total_revenue = revenue_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        total_expenses = expense_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        monthly_revenue = revenue_qs.filter(date__year=today.year, date__month=today.month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        monthly_expenses = expense_qs.filter(date__year=today.year, date__month=today.month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        monthly_profit = monthly_revenue - monthly_expenses
        net_profit = total_revenue - total_expenses

        metrics = [
            {"label": "total_revenue", "display": "Total Revenue", "value": total_revenue},
            {"label": "total_expenses", "display": "Total Expenses", "value": total_expenses},
            {"label": "net_profit", "display": "Net Profit", "value": net_profit},
            {"label": "monthly_revenue", "display": "Monthly Revenue", "value": monthly_revenue},
            {"label": "monthly_expenses", "display": "Monthly Expenses", "value": monthly_expenses},
            {"label": "monthly_profit", "display": "Monthly Profit", "value": monthly_profit},
            {"label": "customers", "display": "Customers", "value": customers_count},
            {"label": "leads", "display": "Leads", "value": leads_count},
            {"label": "today", "display": "Today", "value": today},
        ]
        return metrics
