from django.contrib import admin
from .models import BillingPlan, Subscription, Invoice, Usage, PaymentMethod


@admin.register(BillingPlan)
class BillingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price_monthly', 'price_yearly', 'max_users', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('yearly_discount',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'is_active')
    list_filter = ('status', 'plan', 'start_date')
    search_fields = ('user__email', 'plan__name')
    readonly_fields = ('is_active', 'is_trial')
    date_hierarchy = 'start_date'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'subscription', 'amount', 'currency', 'status', 'due_date')
    list_filter = ('status', 'currency', 'due_date')
    search_fields = ('invoice_number', 'subscription__user__email')
    readonly_fields = ('invoice_number',)
    date_hierarchy = 'created_at'


@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'date', 'users_count', 'patients_count', 'tests_count', 'total_usage_cost')
    list_filter = ('date',)
    search_fields = ('subscription__user__email',)
    readonly_fields = ('total_usage_cost',)
    date_hierarchy = 'date'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'is_default', 'is_active')
    list_filter = ('payment_type', 'is_default', 'is_active')
    search_fields = ('user__email',)