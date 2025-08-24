from django.contrib import admin
from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'paid_until', 'on_trial', 'created_on')
    list_filter = ('on_trial', 'created_on')
    search_fields = ('name',)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain',)