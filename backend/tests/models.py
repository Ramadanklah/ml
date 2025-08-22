"""
Test management models for LIS system.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from samples.models import Sample, SampleType
import uuid
from django.utils import timezone

User = get_user_model()


class TestCategory(models.Model):
    """
    Test categories for organizing laboratory tests.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('category name'), max_length=100, unique=True)
    code = models.CharField(_('category code'), max_length=20, unique=True)
    description = models.TextField(_('description'), blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    # Display and Organization
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    is_active = models.BooleanField(_('is active'), default=True)
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Test Category')
        verbose_name_plural = _('Test Categories')
        db_table = 'test_categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class Test(models.Model):
    """
    Laboratory test definitions and protocols.
    """
    
    # Test Type Choices
    class TestType(models.TextChoices):
        CHEMISTRY = 'CHEMISTRY', _('Chemistry')
        HEMATOLOGY = 'HEMATOLOGY', _('Hematology')
        IMMUNOLOGY = 'IMMUNOLOGY', _('Immunology')
        MICROBIOLOGY = 'MICROBIOLOGY', _('Microbiology')
        MOLECULAR = 'MOLECULAR', _('Molecular')
        PATHOLOGY = 'PATHOLOGY', _('Pathology')
        TOXICOLOGY = 'TOXICOLOGY', _('Toxicology')
        URINALYSIS = 'URINALYSIS', _('Urinalysis')
        OTHER = 'OTHER', _('Other')
    
    # Priority Choices
    class Priority(models.TextChoices):
        ROUTINE = 'ROUTINE', _('Routine')
        URGENT = 'URGENT', _('Urgent')
        STAT = 'STAT', _('STAT')
        CRITICAL = 'CRITICAL', _('Critical')
    
    # Status Choices
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        DISCONTINUED = 'DISCONTINUED', _('Discontinued')
        VALIDATION = 'VALIDATION', _('Validation')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_code = models.CharField(_('test code'), max_length=20, unique=True)
    test_name = models.CharField(_('test name'), max_length=200)
    test_type = models.CharField(_('test type'), max_length=20, choices=TestType.choices)
    category = models.ForeignKey(TestCategory, on_delete=models.PROTECT, related_name='tests')
    
    # Test Information
    description = models.TextField(_('description'), blank=True)
    clinical_indication = models.TextField(_('clinical indication'), blank=True)
    methodology = models.TextField(_('methodology'), blank=True)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Sample Requirements
    sample_types = models.ManyToManyField(SampleType, related_name='tests', blank=True)
    minimum_volume = models.CharField(_('minimum volume'), max_length=50, blank=True)
    volume_unit = models.CharField(_('volume unit'), max_length=20, default='mL')
    special_requirements = models.TextField(_('special requirements'), blank=True)
    
    # Processing Information
    processing_time = models.PositiveIntegerField(_('processing time in hours'), null=True, blank=True)
    priority = models.CharField(_('priority'), max_length=20, choices=Priority.choices, default=Priority.ROUTINE)
    is_automated = models.BooleanField(_('is automated'), default=False)
    
    # Quality Control
    qc_frequency = models.CharField(_('QC frequency'), max_length=100, blank=True)
    qc_materials = models.JSONField(_('QC materials'), default=list, blank=True)
    validation_criteria = models.JSONField(_('validation criteria'), default=dict, blank=True)
    
    # Reference Ranges
    reference_ranges = models.JSONField(_('reference ranges'), default=list, blank=True)
    critical_values = models.JSONField(_('critical values'), default=list, blank=True)
    panic_values = models.JSONField(_('panic values'), default=list, blank=True)
    
    # Cost and Billing
    cost = models.DecimalField(_('cost'), max_digits=10, decimal_places=2, null=True, blank=True)
    billing_code = models.CharField(_('billing code'), max_length=50, blank=True)
    insurance_coverage = models.BooleanField(_('insurance coverage'), default=True)
    
    # Regulatory and Compliance
    regulatory_approval = models.BooleanField(_('regulatory approval'), default=False)
    approval_date = models.DateField(_('approval date'), null=True, blank=True)
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)
    compliance_notes = models.TextField(_('compliance notes'), blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Test')
        verbose_name_plural = _('Tests')
        db_table = 'tests'
        ordering = ['test_code']
        indexes = [
            models.Index(fields=['test_code']),
            models.Index(fields=['test_type']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.test_code} - {self.test_name}"
    
    @property
    def is_expired(self):
        """Check if test approval is expired."""
        if self.expiry_date:
            from datetime import date
            return date.today() > self.expiry_date
        return False


class TestOrder(models.Model):
    """
    Test orders for patient samples.
    """
    
    # Status Choices
    class Status(models.TextChoices):
        ORDERED = 'ORDERED', _('Ordered')
        COLLECTED = 'COLLECTED', _('Collected')
        RECEIVED = 'RECEIVED', _('Received')
        PROCESSING = 'PROCESSING', _('Processing')
        TESTING = 'TESTING', _('Testing')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        REJECTED = 'REJECTED', _('Rejected')
    
    # Priority Choices
    class Priority(models.TextChoices):
        ROUTINE = 'ROUTINE', _('Routine')
        URGENT = 'URGENT', _('Urgent')
        STAT = 'STAT', _('STAT')
        CRITICAL = 'CRITICAL', _('Critical')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.CharField(_('order ID'), max_length=50, unique=True)
    
    # Relationships
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='test_orders')
    test = models.ForeignKey(Test, on_delete=models.PROTECT, related_name='orders')
    
    # Order Information
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.ORDERED)
    priority = models.CharField(_('priority'), max_length=20, choices=Priority.choices, default=Priority.ROUTINE)
    
    # Ordering Information
    ordered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordered_tests')
    ordered_at = models.DateTimeField(_('ordered at'), auto_now_add=True)
    requested_by = models.CharField(_('requested by'), max_length=200, blank=True)
    clinical_notes = models.TextField(_('clinical notes'), blank=True)
    
    # Processing Information
    processing_started_at = models.DateTimeField(_('processing started at'), null=True, blank=True)
    processing_completed_at = models.DateTimeField(_('processing completed at'), null=True, blank=True)
    testing_started_at = models.DateTimeField(_('testing started at'), null=True, blank=True)
    testing_completed_at = models.DateTimeField(_('testing completed at'), null=True, blank=True)
    
    # Results
    result_value = models.TextField(_('result value'), blank=True)
    result_unit = models.CharField(_('result unit'), max_length=50, blank=True)
    result_status = models.CharField(_('result status'), max_length=20, blank=True)
    result_notes = models.TextField(_('result notes'), blank=True)
    
    # Quality Control
    qc_passed = models.BooleanField(_('QC passed'), null=True, blank=True)
    qc_notes = models.TextField(_('QC notes'), blank=True)
    
    # Validation and Approval
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_tests')
    validated_at = models.DateTimeField(_('validated at'), null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_tests')
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Meta
    class Meta:
        verbose_name = _('Test Order')
        verbose_name_plural = _('Test Orders')
        db_table = 'test_orders'
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['ordered_at']),
            models.Index(fields=['sample']),
        ]
    
    def __str__(self):
        return f"{self.order_id} - {self.test.test_name} on {self.sample.sample_id}"
    
    def update_status(self, new_status, user=None, notes=None):
        """Update test order status and log the change."""
        old_status = self.status
        self.status = new_status
        
        # Update timestamps based on status
        if new_status == self.Status.PROCESSING and not self.processing_started_at:
            self.processing_started_at = timezone.now()
        elif new_status == self.Status.TESTING and not self.testing_started_at:
            self.testing_started_at = timezone.now()
        elif new_status == self.Status.COMPLETED and not self.testing_completed_at:
            self.testing_completed_at = timezone.now()
        
        self.save()
        
        # Log status change
        TestOrderStatusLog.objects.create(
            test_order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            notes=notes
        )


class TestOrderStatusLog(models.Model):
    """
    Log of test order status changes for audit purposes.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_order = models.ForeignKey(TestOrder, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(_('old status'), max_length=20)
    new_status = models.CharField(_('new status'), max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(_('changed at'), auto_now_add=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Test Order Status Log')
        verbose_name_plural = _('Test Order Status Logs')
        db_table = 'test_order_status_logs'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.test_order.order_id}: {self.old_status} → {self.new_status}"


class Analyzer(models.Model):
    """
    Laboratory analyzer/instrument information.
    """
    
    # Analyzer Type Choices
    class AnalyzerType(models.TextChoices):
        CHEMISTRY_ANALYZER = 'CHEMISTRY', _('Chemistry Analyzer')
        HEMATOLOGY_ANALYZER = 'HEMATOLOGY', _('Hematology Analyzer')
        IMMUNOASSAY_ANALYZER = 'IMMUNOASSAY', _('Immunoassay Analyzer')
        MOLECULAR_ANALYZER = 'MOLECULAR', _('Molecular Analyzer')
        MICROSCOPE = 'MICROSCOPE', _('Microscope')
        CENTRIFUGE = 'CENTRIFUGE', _('Centrifuge')
        INCUBATOR = 'INCUBATOR', _('Incubator')
        OTHER = 'OTHER', _('Other')
    
    # Status Choices
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
        CALIBRATION = 'CALIBRATION', _('Calibration')
        ERROR = 'ERROR', _('Error')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analyzer_id = models.CharField(_('analyzer ID'), max_length=50, unique=True)
    name = models.CharField(_('analyzer name'), max_length=200)
    analyzer_type = models.CharField(_('analyzer type'), max_length=20, choices=AnalyzerType.choices)
    
    # Manufacturer Information
    manufacturer = models.CharField(_('manufacturer'), max_length=100)
    model = models.CharField(_('model'), max_length=100)
    serial_number = models.CharField(_('serial number'), max_length=100, blank=True)
    software_version = models.CharField(_('software version'), max_length=50, blank=True)
    
    # Location and Status
    location = models.CharField(_('location'), max_length=200, blank=True)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Capabilities
    supported_tests = models.ManyToManyField(Test, related_name='analyzers', blank=True)
    throughput = models.CharField(_('throughput'), max_length=100, blank=True)
    sample_capacity = models.PositiveIntegerField(_('sample capacity'), null=True, blank=True)
    
    # Maintenance and Calibration
    last_maintenance = models.DateField(_('last maintenance'), null=True, blank=True)
    next_maintenance = models.DateField(_('next maintenance'), null=True, blank=True)
    last_calibration = models.DateField(_('last calibration'), null=True, blank=True)
    next_calibration = models.DateField(_('next calibration'), null=True, blank=True)
    
    # Quality Control
    qc_frequency = models.CharField(_('QC frequency'), max_length=100, blank=True)
    qc_materials = models.JSONField(_('QC materials'), default=list, blank=True)
    
    # Communication
    interface_type = models.CharField(_('interface type'), max_length=50, blank=True)
    communication_protocol = models.CharField(_('communication protocol'), max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    port = models.PositiveIntegerField(_('port'), null=True, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Analyzer')
        verbose_name_plural = _('Analyzers')
        db_table = 'analyzers'
        ordering = ['analyzer_type', 'name']
        indexes = [
            models.Index(fields=['analyzer_id']),
            models.Index(fields=['analyzer_type']),
            models.Index(fields=['status']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.analyzer_id})"
    
    @property
    def is_due_maintenance(self):
        """Check if analyzer is due for maintenance."""
        if self.next_maintenance:
            from datetime import date
            return date.today() >= self.next_maintenance
        return False
    
    @property
    def is_due_calibration(self):
        """Check if analyzer is due for calibration."""
        if self.next_calibration:
            from datetime import date
            return date.today() >= self.next_calibration
        return False


class QualityControl(models.Model):
    """
    Quality control procedures and results.
    """
    
    # QC Type Choices
    class QCType(models.TextChoices):
        DAILY = 'DAILY', _('Daily')
        WEEKLY = 'WEEKLY', _('Weekly')
        MONTHLY = 'MONTHLY', _('Monthly')
        CALIBRATION = 'CALIBRATION', _('Calibration')
        VERIFICATION = 'VERIFICATION', _('Verification')
        OTHER = 'OTHER', _('Other')
    
    # Status Choices
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        PASSED = 'PASSED', _('Passed')
        FAILED = 'FAILED', _('Failed')
        OUT_OF_RANGE = 'OUT_OF_RANGE', _('Out of Range')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qc_id = models.CharField(_('QC ID'), max_length=50, unique=True)
    
    # Relationships
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='quality_controls')
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE, related_name='quality_controls', null=True, blank=True)
    
    # QC Information
    qc_type = models.CharField(_('QC type'), max_length=20, choices=QCType.choices)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Materials and Procedures
    qc_material = models.CharField(_('QC material'), max_length=200, blank=True)
    lot_number = models.CharField(_('lot number'), max_length=100, blank=True)
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)
    
    # Results
    expected_value = models.CharField(_('expected value'), max_length=100, blank=True)
    actual_value = models.CharField(_('actual value'), max_length=100, blank=True)
    unit = models.CharField(_('unit'), max_length=50, blank=True)
    tolerance = models.CharField(_('tolerance'), max_length=100, blank=True)
    
    # Performance
    mean = models.DecimalField(_('mean'), max_digits=10, decimal_places=4, null=True, blank=True)
    standard_deviation = models.DecimalField(_('standard deviation'), max_digits=10, decimal_places=4, null=True, blank=True)
    coefficient_of_variation = models.DecimalField(_('coefficient of variation'), max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Execution
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    performed_at = models.DateTimeField(_('performed at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    # Notes and Comments
    notes = models.TextField(_('notes'), blank=True)
    corrective_actions = models.TextField(_('corrective actions'), blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Quality Control')
        verbose_name_plural = _('Quality Controls')
        db_table = 'quality_controls'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['qc_id']),
            models.Index(fields=['qc_type']),
            models.Index(fields=['status']),
            models.Index(fields=['performed_at']),
            models.Index(fields=['test']),
        ]
    
    def __str__(self):
        return f"{self.qc_id} - {self.test.test_name} ({self.qc_type})"
    
    @property
    def is_expired(self):
        """Check if QC material is expired."""
        if self.expiry_date:
            from datetime import date
            return date.today() > self.expiry_date
        return False
    
    def calculate_statistics(self):
        """Calculate QC statistics if multiple results exist."""
        # This would be implemented based on historical QC data
        pass