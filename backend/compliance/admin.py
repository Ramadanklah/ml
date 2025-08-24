from django.contrib import admin
from .models import LOINC, ICD10GM, OPS, EBM, GOAE, GermanInsuranceCode


@admin.register(LOINC)
class LOINCAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'component', 'system')
    list_filter = ('scale_type', 'method_type')
    search_fields = ('code', 'name', 'component')


@admin.register(ICD10GM)
class ICD10GMAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'year')
    list_filter = ('category', 'year')
    search_fields = ('code', 'name')


@admin.register(OPS)
class OPSAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'year')
    list_filter = ('category', 'year')
    search_fields = ('code', 'name')


@admin.register(EBM)
class EBMAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'points', 'category')
    list_filter = ('category',)
    search_fields = ('code', 'name')


@admin.register(GOAE)
class GOAEAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'fee', 'category')
    list_filter = ('category',)
    search_fields = ('code', 'name')


@admin.register(GermanInsuranceCode)
class GermanInsuranceCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'insurance_type', 'coverage')
    list_filter = ('insurance_type', 'coverage')
    search_fields = ('code', 'name')