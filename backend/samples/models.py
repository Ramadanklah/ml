"""
Sample management models for LIS system.
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class Patient(models.Model):
    """
    Patient information model for sample tracking.
    """
    
    # Gender Choices
    class Gender(models.TextChoices):
        MALE = 'M', _('Male')
        FEMALE = 'F', _('Female')
        OTHER = 'O', _('Other')
        UNKNOWN = 'U', _('Unknown')
    
    # Blood Type Choices
    class BloodType(models.TextChoices):
        A_POSITIVE = 'A+', _('A+')
        A_NEGATIVE = 'A-', _('A-')
        B_POSITIVE = 'B+', _('B+')
        B_NEGATIVE = 'B-', _('B-')
        AB_POSITIVE = 'AB+', _('AB+')
        AB_NEGATIVE = 'AB-', _('AB-')
        O_POSITIVE = 'O+', _('O+')
        O_NEGATIVE = 'O-', _('O-')
        UNKNOWN = 'UNK', _('Unknown')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.CharField(_('patient ID'), max_length=50, unique=True)
    mrn = models.CharField(_('medical record number'), max_length=50, unique=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    middle_name = models.CharField(_('middle name'), max_length=150, blank=True)
    date_of_birth = models.DateField(_('date of birth'))
    gender = models.CharField(_('gender'), max_length=1, choices=Gender.choices)
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(_('email'), blank=True)
    address = models.TextField(_('address'), blank=True)
    
    # Medical Information
    blood_type = models.CharField(_('blood type'), max_length=3, choices=BloodType.choices, blank=True)
    allergies = models.JSONField(_('allergies'), default=list, blank=True)
    medications = models.JSONField(_('current medications'), default=list, blank=True)
    medical_history = models.JSONField(_('medical history'), default=list, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(_('emergency contact name'), max_length=255, blank=True)
    emergency_contact_phone = models.CharField(_('emergency contact phone'), max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(_('emergency contact relationship'), max_length=100, blank=True)
    
    # Insurance & Billing
    insurance_provider = models.CharField(_('insurance provider'), max_length=100, blank=True)
    insurance_policy_number = models.CharField(_('insurance policy number'), max_length=100, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')
        db_table = 'patients'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['mrn']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.patient_id})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        if self.middle_name:
            full_name = f"{self.first_name} {self.middle_name} {self.last_name}"
        return full_name.strip()
    
    def get_age(self):
        """Calculate patient age."""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class SampleType(models.Model):
    """
    Sample type definitions for different laboratory tests.
    """
    
    # Collection Method Choices
    class CollectionMethod(models.TextChoices):
        VENIPUNCTURE = 'VENIPUNCTURE', _('Venipuncture')
        FINGER_STICK = 'FINGER_STICK', _('Finger Stick')
        URINE_COLLECTION = 'URINE_COLLECTION', _('Urine Collection')
        STOOL_COLLECTION = 'STOOL_COLLECTION', _('Stool Collection')
        SWAB = 'SWAB', _('Swab')
        TISSUE_BIOPSY = 'TISSUE_BIOPSY', _('Tissue Biopsy')
        FLUID_ASPIRATION = 'FLUID_ASPIRATION', _('Fluid Aspiration')
        OTHER = 'OTHER', _('Other')
    
    # Processing Type Choices
    class ProcessingType(models.TextChoices):
        ROUTINE = 'ROUTINE', _('Routine')
        STAT = 'STAT', _('STAT')
        URGENT = 'URGENT', _('Urgent')
        RESEARCH = 'RESEARCH', _('Research')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('sample type name'), max_length=100, unique=True)
    code = models.CharField(_('sample type code'), max_length=20, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # Collection Information
    collection_method = models.CharField(_('collection method'), max_length=20, choices=CollectionMethod.choices)
    collection_instructions = models.TextField(_('collection instructions'), blank=True)
    required_volume = models.CharField(_('required volume'), max_length=50, blank=True)
    minimum_volume = models.CharField(_('minimum volume'), max_length=50, blank=True)
    
    # Processing Information
    processing_type = models.CharField(_('processing type'), max_length=20, choices=ProcessingType.choices, default=ProcessingType.ROUTINE)
    processing_time = models.PositiveIntegerField(_('processing time in hours'), null=True, blank=True)
    storage_requirements = models.JSONField(_('storage requirements'), default=dict, blank=True)
    
    # Container Information
    container_type = models.CharField(_('container type'), max_length=100, blank=True)
    container_color = models.CharField(_('container color'), max_length=50, blank=True)
    additives = models.JSONField(_('additives'), default=list, blank=True)
    
    # Special Handling
    special_handling = models.TextField(_('special handling instructions'), blank=True)
    hazardous = models.BooleanField(_('hazardous material'), default=False)
    biohazard_level = models.CharField(_('biohazard level'), max_length=10, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Sample Type')
        verbose_name_plural = _('Sample Types')
        db_table = 'sample_types'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Sample(models.Model):
    """
    Sample model for tracking individual samples through the laboratory.
    """
    
    # Status Choices
    class Status(models.TextChoices):
        COLLECTED = 'COLLECTED', _('Collected')
        RECEIVED = 'RECEIVED', _('Received')
        PROCESSING = 'PROCESSING', _('Processing')
        TESTING = 'TESTING', _('Testing')
        COMPLETED = 'COMPLETED', _('Completed')
        REJECTED = 'REJECTED', _('Rejected')
        CANCELLED = 'CANCELLED', _('Cancelled')
        DISPOSED = 'DISPOSED', _('Disposed')
    
    # Priority Choices
    class Priority(models.TextChoices):
        ROUTINE = 'ROUTINE', _('Routine')
        URGENT = 'URGENT', _('Urgent')
        STAT = 'STAT', _('STAT')
        CRITICAL = 'CRITICAL', _('Critical')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample_id = models.CharField(_('sample ID'), max_length=50, unique=True)
    barcode = models.CharField(_('barcode'), max_length=100, unique=True)
    
    # Relationships
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='samples')
    sample_type = models.ForeignKey(SampleType, on_delete=models.PROTECT, related_name='samples')
    
    # Sample Information
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.COLLECTED)
    priority = models.CharField(_('priority'), max_length=20, choices=Priority.choices, default=Priority.ROUTINE)
    
    # Collection Information
    collection_date = models.DateTimeField(_('collection date'))
    collection_location = models.CharField(_('collection location'), max_length=200, blank=True)
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_samples')
    
    # Sample Details
    volume = models.DecimalField(_('volume'), max_digits=8, decimal_places=2, null=True, blank=True)
    volume_unit = models.CharField(_('volume unit'), max_length=20, default='mL')
    appearance = models.CharField(_('appearance'), max_length=200, blank=True)
    color = models.CharField(_('color'), max_length=50, blank=True)
    turbidity = models.CharField(_('turbidity'), max_length=50, blank=True)
    
    # Processing Information
    received_date = models.DateTimeField(_('received date'), null=True, blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_samples')
    processing_start_date = models.DateTimeField(_('processing start date'), null=True, blank=True)
    processing_complete_date = models.DateTimeField(_('processing complete date'), null=True, blank=True)
    
    # Storage Information
    storage_location = models.CharField(_('storage location'), max_length=200, blank=True)
    storage_temperature = models.CharField(_('storage temperature'), max_length=50, blank=True)
    storage_conditions = models.JSONField(_('storage conditions'), default=dict, blank=True)
    
    # Quality Control
    quality_notes = models.TextField(_('quality notes'), blank=True)
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    rejection_date = models.DateTimeField(_('rejection date'), null=True, blank=True)
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_samples')
    
    # Chain of Custody
    chain_of_custody = models.JSONField(_('chain of custody'), default=list, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_samples')
    
    # Meta
    class Meta:
        verbose_name = _('Sample')
        verbose_name_plural = _('Samples')
        db_table = 'samples'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sample_id']),
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['collection_date']),
            models.Index(fields=['patient']),
        ]
    
    def __str__(self):
        return f"{self.sample_id} - {self.patient.get_full_name()}"
    
    def generate_barcode(self):
        """Generate a unique barcode for the sample."""
        import barcode
        from barcode.writer import ImageWriter
        
        # Generate barcode using sample ID
        barcode_class = barcode.get_barcode_class('code128')
        barcode_instance = barcode_class(self.sample_id, writer=ImageWriter())
        
        # Save barcode image
        filename = f"barcodes/{self.sample_id}"
        barcode_instance.save(filename)
        
        return filename
    
    def update_status(self, new_status, user=None, notes=None):
        """Update sample status and log the change."""
        old_status = self.status
        self.status = new_status
        
        # Update timestamps based on status
        if new_status == self.Status.RECEIVED and not self.received_date:
            self.received_date = timezone.now()
            self.received_by = user
        elif new_status == self.Status.PROCESSING and not self.processing_start_date:
            self.processing_start_date = timezone.now()
        elif new_status == self.Status.COMPLETED and not self.processing_complete_date:
            self.processing_complete_date = timezone.now()
        
        self.save()
        
        # Log status change
        SampleStatusLog.objects.create(
            sample=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            notes=notes
        )
    
    def add_chain_of_custody_entry(self, action, user, location=None, notes=None):
        """Add a chain of custody entry."""
        entry = {
            'timestamp': timezone.now().isoformat(),
            'action': action,
            'user_id': str(user.id),
            'user_name': user.get_full_name(),
            'location': location,
            'notes': notes
        }
        
        if not self.chain_of_custody:
            self.chain_of_custody = []
        
        self.chain_of_custody.append(entry)
        self.save(update_fields=['chain_of_custody'])


class SampleStatusLog(models.Model):
    """
    Log of sample status changes for audit purposes.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(_('old status'), max_length=20)
    new_status = models.CharField(_('new status'), max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(_('changed at'), auto_now_add=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Sample Status Log')
        verbose_name_plural = _('Sample Status Logs')
        db_table = 'sample_status_logs'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.sample.sample_id}: {self.old_status} → {self.new_status}"


class SampleContainer(models.Model):
    """
    Container information for sample storage and tracking.
    """
    
    # Container Type Choices
    class ContainerType(models.TextChoices):
        VACUTAINER = 'VACUTAINER', _('Vacutainer')
        URINE_CUP = 'URINE_CUP', _('Urine Cup')
        STOOL_CONTAINER = 'STOOL_CONTAINER', _('Stool Container')
        SWAB_TUBE = 'SWAB_TUBE', _('Swab Tube')
        BIOPSY_CONTAINER = 'BIOPSY_CONTAINER', _('Biopsy Container')
        FLUID_CONTAINER = 'FLUID_CONTAINER', _('Fluid Container')
        OTHER = 'OTHER', _('Other')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    container_id = models.CharField(_('container ID'), max_length=50, unique=True)
    container_type = models.CharField(_('container type'), max_length=20, choices=ContainerType.choices)
    manufacturer = models.CharField(_('manufacturer'), max_length=100, blank=True)
    model = models.CharField(_('model'), max_length=100, blank=True)
    lot_number = models.CharField(_('lot number'), max_length=100, blank=True)
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)
    
    # Specifications
    volume_capacity = models.DecimalField(_('volume capacity'), max_digits=8, decimal_places=2, null=True, blank=True)
    volume_unit = models.CharField(_('volume unit'), max_length=20, default='mL')
    color = models.CharField(_('color'), max_length=50, blank=True)
    additives = models.JSONField(_('additives'), default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    is_sterile = models.BooleanField(_('is sterile'), default=True)
    
    # Meta
    class Meta:
        verbose_name = _('Sample Container')
        verbose_name_plural = _('Sample Containers')
        db_table = 'sample_containers'
        ordering = ['container_type', 'manufacturer']
    
    def __str__(self):
        return f"{self.container_type} - {self.manufacturer} ({self.container_id})"
    
    @property
    def is_expired(self):
        """Check if container is expired."""
        if self.expiry_date:
            from datetime import date
            return date.today() > self.expiry_date
        return False