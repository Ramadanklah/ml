from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Vendor(models.Model):
    """Laboratory analyzer vendors"""
    VENDOR_TYPES = [
        ('roche', 'Roche'),
        ('siemens', 'Siemens'),
        ('abbott', 'Abbott'),
        ('beckman', 'Beckman'),
        ('sysmex', 'Sysmex'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES)
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Germany')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_vendor_type_display()})"


class AnalyzerModel(models.Model):
    """Specific analyzer models from vendors"""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='analyzer_models')
    model_name = models.CharField(max_length=100)
    model_number = models.CharField(max_length=50)
    description = models.TextField()
    release_date = models.DateField(null=True, blank=True)
    is_discontinued = models.BooleanField(default=False)
    specifications = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['vendor', 'model_name']
        unique_together = ['vendor', 'model_number']
    
    def __str__(self):
        return f"{self.vendor.name} {self.model_name}"


class Interface(models.Model):
    """Interface types for analyzer communication"""
    INTERFACE_TYPES = [
        ('astm', 'ASTM'),
        ('hl7', 'HL7'),
        ('lis', 'LIS'),
        ('ftp', 'FTP'),
        ('api', 'API'),
        ('serial', 'Serial'),
        ('ethernet', 'Ethernet'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    interface_type = models.CharField(max_length=20, choices=INTERFACE_TYPES)
    version = models.CharField(max_length=20)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class TestMapping(models.Model):
    """Mapping between analyzer tests and LIS tests"""
    analyzer_model = models.ForeignKey(AnalyzerModel, on_delete=models.CASCADE, related_name='test_mappings')
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE, related_name='test_mappings')
    analyzer_test_code = models.CharField(max_length=50)
    analyzer_test_name = models.CharField(max_length=200)
    lis_test_code = models.CharField(max_length=50)
    lis_test_name = models.CharField(max_length=200)
    unit_conversion = models.CharField(max_length=100, blank=True)
    reference_range_mapping = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['analyzer_model', 'analyzer_test_code']
        unique_together = ['analyzer_model', 'analyzer_test_code', 'interface']
    
    def __str__(self):
        return f"{self.analyzer_model} - {self.analyzer_test_code} → {self.lis_test_code}"


class ConnectionProfile(models.Model):
    """Connection profiles for analyzer integration"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
        ('error', 'Error'),
    ]
    
    name = models.CharField(max_length=100)
    analyzer_model = models.ForeignKey(AnalyzerModel, on_delete=models.CASCADE, related_name='connection_profiles')
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE, related_name='connection_profiles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    connection_string = models.TextField()
    credentials = models.JSONField(default=dict)
    settings = models.JSONField(default=dict)
    last_connection = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.analyzer_model}"


class DataTransferLog(models.Model):
    """Log of data transfers from analyzers"""
    TRANSFER_TYPES = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('sync', 'Synchronization'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
        ('pending', 'Pending'),
    ]
    
    connection_profile = models.ForeignKey(ConnectionProfile, on_delete=models.CASCADE, related_name='transfer_logs')
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    records_processed = models.PositiveIntegerField(default=0)
    records_successful = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.connection_profile} - {self.transfer_type} ({self.status})"
    
    @property
    def duration(self):
        """Calculate transfer duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.records_processed > 0:
            return (self.records_successful / self.records_processed) * 100
        return 0


class QualityControl(models.Model):
    """Quality control data from analyzers"""
    QC_TYPES = [
        ('level_1', 'Level 1 (Low)'),
        ('level_2', 'Level 2 (Medium)'),
        ('level_3', 'Level 3 (High)'),
    ]
    
    analyzer_model = models.ForeignKey(AnalyzerModel, on_delete=models.CASCADE, related_name='quality_controls')
    qc_type = models.CharField(max_length=20, choices=QC_TYPES)
    test_code = models.CharField(max_length=50)
    test_name = models.CharField(max_length=200)
    expected_value = models.DecimalField(max_digits=10, decimal_places=4)
    measured_value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=20)
    acceptable_range_low = models.DecimalField(max_digits=10, decimal_places=4)
    acceptable_range_high = models.DecimalField(max_digits=10, decimal_places=4)
    is_acceptable = models.BooleanField()
    run_date = models.DateTimeField()
    operator = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-run_date']
    
    def __str__(self):
        return f"{self.analyzer_model} {self.test_name} - {self.run_date.date()}"
    
    @property
    def deviation_percentage(self):
        """Calculate deviation from expected value"""
        if self.expected_value != 0:
            deviation = abs(self.measured_value - self.expected_value)
            return (deviation / self.expected_value) * 100
        return 0