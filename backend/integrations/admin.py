from django.contrib import admin
from .models import (
    Vendor, AnalyzerModel, Interface, TestMapping, 
    ConnectionProfile, DataTransferLog, QualityControl
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor_type', 'country', 'is_active')
    list_filter = ('vendor_type', 'country', 'is_active')
    search_fields = ('name', 'contact_email')


@admin.register(AnalyzerModel)
class AnalyzerModelAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'vendor', 'model_number', 'release_date', 'is_discontinued')
    list_filter = ('vendor', 'is_discontinued', 'release_date')
    search_fields = ('model_name', 'model_number', 'description')
    date_hierarchy = 'release_date'


@admin.register(Interface)
class InterfaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'interface_type', 'version', 'is_active')
    list_filter = ('interface_type', 'is_active')
    search_fields = ('name', 'description')


@admin.register(TestMapping)
class TestMappingAdmin(admin.ModelAdmin):
    list_display = ('analyzer_model', 'interface', 'analyzer_test_code', 'lis_test_code', 'is_active')
    list_filter = ('analyzer_model', 'interface', 'is_active')
    search_fields = ('analyzer_test_code', 'lis_test_code', 'analyzer_test_name')


@admin.register(ConnectionProfile)
class ConnectionProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'analyzer_model', 'interface', 'status', 'last_connection')
    list_filter = ('status', 'analyzer_model', 'interface')
    search_fields = ('name',)
    readonly_fields = ('last_connection', 'last_error')


@admin.register(DataTransferLog)
class DataTransferLogAdmin(admin.ModelAdmin):
    list_display = ('connection_profile', 'transfer_type', 'status', 'start_time', 'records_processed', 'success_rate')
    list_filter = ('transfer_type', 'status', 'start_time')
    search_fields = ('connection_profile__name',)
    readonly_fields = ('duration', 'success_rate')
    date_hierarchy = 'start_time'


@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = ('analyzer_model', 'test_name', 'qc_type', 'expected_value', 'measured_value', 'is_acceptable', 'run_date')
    list_filter = ('qc_type', 'is_acceptable', 'run_date', 'analyzer_model')
    search_fields = ('test_name', 'test_code')
    readonly_fields = ('deviation_percentage',)
    date_hierarchy = 'run_date'