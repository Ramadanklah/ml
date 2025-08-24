from django.db import models


class LOINC(models.Model):
    """LOINC (Logical Observation Identifiers Names and Codes)"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=500)
    component = models.CharField(max_length=200)
    property = models.CharField(max_length=200)
    time_aspect = models.CharField(max_length=200)
    system = models.CharField(max_length=200)
    scale_type = models.CharField(max_length=200)
    method_type = models.CharField(max_length=200)
    
    class Meta:
        verbose_name = "LOINC Code"
        verbose_name_plural = "LOINC Codes"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ICD10GM(models.Model):
    """ICD-10-GM (German Modification of ICD-10)"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=500)
    category = models.CharField(max_length=200)
    year = models.IntegerField()
    
    class Meta:
        verbose_name = "ICD-10-GM Code"
        verbose_name_plural = "ICD-10-GM Codes"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class OPS(models.Model):
    """OPS (Operation and Procedure Classification System)"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=500)
    category = models.CharField(max_length=200)
    year = models.IntegerField()
    
    class Meta:
        verbose_name = "OPS Code"
        verbose_name_plural = "OPS Codes"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class EBM(models.Model):
    """EBM (Einheitlicher Bewertungsmaßstab) - German Medical Fee Schedule"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=500)
    points = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=200)
    
    class Meta:
        verbose_name = "EBM Code"
        verbose_name_plural = "EBM Codes"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class GOAE(models.Model):
    """GOÄ (Gebührenordnung für Ärzte) - German Medical Fee Schedule"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=500)
    fee = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=200)
    
    class Meta:
        verbose_name = "GOÄ Code"
        verbose_name_plural = "GOÄ Codes"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class GermanInsuranceCode(models.Model):
    """German Insurance Codes for Laboratory Tests"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=500)
    insurance_type = models.CharField(max_length=100)
    coverage = models.CharField(max_length=200)
    
    class Meta:
        verbose_name = "German Insurance Code"
        verbose_name_plural = "German Insurance Codes"
    
    def __str__(self):
        return f"{self.code} - {self.name}"