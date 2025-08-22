"""
Test Results management models for LIS system with LDT integration.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from samples.models import Sample, Patient
from tests.models import Test, TestOrder
import uuid
import json

User = get_user_model()


class ResultStatus(models.Model):
    """
    Result status definitions for workflow management.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('status name'), max_length=50, unique=True)
    code = models.CharField(_('status code'), max_length=20, unique=True)
    description = models.TextField(_('description'), blank=True)
    color = models.CharField(_('color'), max_length=7, default='#000000')
    is_final = models.BooleanField(_('is final status'), default=False)
    requires_review = models.BooleanField(_('requires review'), default=False)
    can_edit = models.BooleanField(_('can edit'), default=True)
    
    # Workflow transitions
    allowed_transitions = models.JSONField(_('allowed transitions'), default=list, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Result Status')
        verbose_name_plural = _('Result Statuses')
        db_table = 'result_statuses'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TestResult(models.Model):
    """
    Comprehensive test result model with LDT integration support.
    """
    
    # Result Type Choices
    class ResultType(models.TextChoices):
        NUMERIC = 'NUMERIC', _('Numeric')
        TEXT = 'TEXT', _('Text')
        POSITIVE_NEGATIVE = 'POSITIVE_NEGATIVE', _('Positive/Negative')
        POSITIVE_NEGATIVE_INDETERMINATE = 'POSITIVE_NEGATIVE_INDETERMINATE', _('Positive/Negative/Indeterminate')
        REACTIVE_NONREACTIVE = 'REACTIVE_NONREACTIVE', _('Reactive/Nonreactive')
        HIGH_NORMAL_LOW = 'HIGH_NORMAL_LOW', _('High/Normal/Low')
        CRITICAL = 'CRITICAL', _('Critical')
        SEMI_QUANTITATIVE = 'SEMI_QUANTITATIVE', _('Semi-Quantitative')
        QUANTITATIVE = 'QUANTITATIVE', _('Quantitative')
        MORPHOLOGY = 'MORPHOLOGY', _('Morphology')
        IMAGE = 'IMAGE', _('Image')
        FILE = 'FILE', _('File')
        OTHER = 'OTHER', _('Other')
    
    # Critical Level Choices
    class CriticalLevel(models.TextChoices):
        NORMAL = 'NORMAL', _('Normal')
        LOW = 'LOW', _('Low')
        HIGH = 'HIGH', _('High')
        CRITICAL_LOW = 'CRITICAL_LOW', _('Critical Low')
        CRITICAL_HIGH = 'CRITICAL_HIGH', _('Critical High')
        PANIC_LOW = 'PANIC_LOW', _('Panic Low')
        PANIC_HIGH = 'PANIC_HIGH', _('Panic High')
        ABNORMAL = 'ABNORMAL', _('Abnormal')
        POSITIVE = 'POSITIVE', _('Positive')
        NEGATIVE = 'NEGATIVE', _('Negative')
        INDETERMINATE = 'INDETERMINATE', _('Indeterminate')
        REACTIVE = 'REACTIVE', _('Reactive')
        NONREACTIVE = 'NONREACTIVE', _('Nonreactive')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result_id = models.CharField(_('result ID'), max_length=50, unique=True)
    
    # Relationships
    test_order = models.ForeignKey(TestOrder, on_delete=models.CASCADE, related_name='results')
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='results')
    test = models.ForeignKey(Test, on_delete=models.PROTECT, related_name='results')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='results')
    
    # Result Information
    result_type = models.CharField(_('result type'), max_length=30, choices=ResultType.choices)
    result_value = models.TextField(_('result value'))
    result_unit = models.CharField(_('result unit'), max_length=50, blank=True)
    critical_level = models.CharField(_('critical level'), max_length=20, choices=CriticalLevel.choices, blank=True)
    
    # Numeric Results
    numeric_value = models.DecimalField(_('numeric value'), max_digits=15, decimal_places=6, null=True, blank=True)
    reference_range_low = models.DecimalField(_('reference range low'), max_digits=15, decimal_places=6, null=True, blank=True)
    reference_range_high = models.DecimalField(_('reference range high'), max_digits=15, decimal_places=6, null=True, blank=True)
    reference_range_unit = models.CharField(_('reference range unit'), max_length=50, blank=True)
    
    # LDT Integration
    ldt_message_id = models.CharField(_('LDT message ID'), max_length=100, blank=True)
    ldt_sequence_number = models.PositiveIntegerField(_('LDT sequence number'), null=True, blank=True)
    ldt_obr_sequence = models.PositiveIntegerField(_('LDT OBR sequence'), null=True, blank=True)
    ldt_obx_sequence = models.PositiveIntegerField(_('LDT OBX sequence'), null=True, blank=True)
    ldt_raw_data = models.JSONField(_('LDT raw data'), default=dict, blank=True)
    ldt_parsed_data = models.JSONField(_('LDT parsed data'), default=dict, blank=True)
    ldt_processing_status = models.CharField(_('LDT processing status'), max_length=20, default='PENDING')
    ldt_error_message = models.TextField(_('LDT error message'), blank=True)
    
    # Quality Control
    qc_status = models.CharField(_('QC status'), max_length=20, default='PENDING')
    qc_notes = models.TextField(_('QC notes'), blank=True)
    qc_performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='qc_results')
    qc_performed_at = models.DateTimeField(_('QC performed at'), null=True, blank=True)
    
    # Validation and Approval
    validation_status = models.CharField(_('validation status'), max_length=20, default='PENDING')
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_results')
    validated_at = models.DateTimeField(_('validated at'), null=True, blank=True)
    validation_notes = models.TextField(_('validation notes'), blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_results')
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    approval_notes = models.TextField(_('approval notes'), blank=True)
    
    # Clinical Information
    clinical_significance = models.TextField(_('clinical significance'), blank=True)
    interpretation = models.TextField(_('interpretation'), blank=True)
    recommendations = models.TextField(_('recommendations'), blank=True)
    clinical_notes = models.TextField(_('clinical notes'), blank=True)
    
    # Technical Information
    methodology = models.CharField(_('methodology'), max_length=200, blank=True)
    instrument = models.CharField(_('instrument'), max_length=200, blank=True)
    reagent_lot = models.CharField(_('reagent lot'), max_length=100, blank=True)
    calibration_date = models.DateTimeField(_('calibration date'), null=True, blank=True)
    
    # Result Processing
    result_date = models.DateTimeField(_('result date'), auto_now_add=True)
    result_entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='entered_results')
    result_entered_at = models.DateTimeField(_('result entered at'), auto_now_add=True)
    
    # Status and Workflow
    status = models.ForeignKey(ResultStatus, on_delete=models.PROTECT, related_name='results')
    workflow_step = models.CharField(_('workflow step'), max_length=100, default='RESULT_ENTRY')
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_results')
    
    # Meta
    class Meta:
        verbose_name = _('Test Result')
        verbose_name_plural = _('Test Results')
        db_table = 'test_results'
        ordering = ['-result_date']
        indexes = [
            models.Index(fields=['result_id']),
            models.Index(fields=['ldt_message_id']),
            models.Index(fields=['status']),
            models.Index(fields=['result_date']),
            models.Index(fields=['test_order']),
            models.Index(fields=['patient']),
            models.Index(fields=['critical_level']),
        ]
    
    def __str__(self):
        return f"{self.result_id} - {self.test.test_name}: {self.result_value}"
    
    @property
    def is_critical(self):
        """Check if result is critical."""
        return self.critical_level in [
            self.CriticalLevel.CRITICAL_LOW,
            self.CriticalLevel.CRITICAL_HIGH,
            self.CriticalLevel.PANIC_LOW,
            self.CriticalLevel.PANIC_HIGH,
        ]
    
    @property
    def is_abnormal(self):
        """Check if result is abnormal."""
        if self.numeric_value and self.reference_range_low and self.reference_range_high:
            return (self.numeric_value < self.reference_range_low or 
                   self.numeric_value > self.reference_range_high)
        return self.critical_level != self.CriticalLevel.NORMAL
    
    @property
    def reference_range_display(self):
        """Get formatted reference range."""
        if self.reference_range_low and self.reference_range_high:
            return f"{self.reference_range_low} - {self.reference_range_high} {self.reference_range_unit}"
        return ""
    
    def process_ldt_data(self, ldt_data):
        """Process LDT data and update result."""
        try:
            self.ldt_raw_data = ldt_data
            self.ldt_parsed_data = self._parse_ldt_data(ldt_data)
            self.ldt_processing_status = 'PROCESSED'
            self.save()
            return True
        except Exception as e:
            self.ldt_processing_status = 'ERROR'
            self.ldt_error_message = str(e)
            self.save()
            return False
    
    def _parse_ldt_data(self, ldt_data):
        """Parse LDT data into structured format."""
        # This would implement LDT parsing logic
        # LDT format: OBX|1|NM|GLU^GLU|1|120|mg/dL|70-110|H|F|||20231201120000
        parsed = {}
        
        if isinstance(ldt_data, str):
            # Parse LDT string format
            parts = ldt_data.split('|')
            if len(parts) >= 8:
                parsed = {
                    'sequence': parts[1] if len(parts) > 1 else '',
                    'value_type': parts[2] if len(parts) > 2 else '',
                    'test_code': parts[3] if len(parts) > 3 else '',
                    'sequence_number': parts[4] if len(parts) > 4 else '',
                    'value': parts[5] if len(parts) > 5 else '',
                    'unit': parts[6] if len(parts) > 6 else '',
                    'reference_range': parts[7] if len(parts) > 7 else '',
                    'abnormal_flag': parts[8] if len(parts) > 8 else '',
                    'status': parts[9] if len(parts) > 9 else '',
                    'timestamp': parts[14] if len(parts) > 14 else '',
                }
        
        return parsed


class LDTMessage(models.Model):
    """
    LDT (Lab Data Transfer) message management for Mirth Connect integration.
    """
    
    # Message Status Choices
    class Status(models.TextChoices):
        RECEIVED = 'RECEIVED', _('Received')
        PROCESSING = 'PROCESSING', _('Processing')
        PROCESSED = 'PROCESSED', _('Processed')
        ERROR = 'ERROR', _('Error')
        REJECTED = 'REJECTED', _('Rejected')
        PENDING_REVIEW = 'PENDING_REVIEW', _('Pending Review')
    
    # Message Type Choices
    class MessageType(models.TextChoices):
        RESULT = 'RESULT', _('Result')
        ORDER = 'ORDER', _('Order')
        QUERY = 'QUERY', _('Query')
        RESPONSE = 'RESPONSE', _('Response')
        ACK = 'ACK', _('Acknowledgment')
        NACK = 'NACK', _('Negative Acknowledgment')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_id = models.CharField(_('message ID'), max_length=100, unique=True)
    mirth_message_id = models.CharField(_('Mirth message ID'), max_length=100, blank=True)
    
    # Message Information
    message_type = models.CharField(_('message type'), max_length=20, choices=MessageType.choices)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.RECEIVED)
    
    # LDT Specific
    ldt_version = models.CharField(_('LDT version'), max_length=20, blank=True)
    sending_facility = models.CharField(_('sending facility'), max_length=100, blank=True)
    receiving_facility = models.CharField(_('receiving facility'), max_length=100, blank=True)
    message_control_id = models.CharField(_('message control ID'), max_length=100, blank=True)
    
    # Content
    raw_message = models.TextField(_('raw message'))
    parsed_message = models.JSONField(_('parsed message'), default=dict, blank=True)
    message_structure = models.JSONField(_('message structure'), default=dict, blank=True)
    
    # Processing
    received_at = models.DateTimeField(_('received at'), auto_now_add=True)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    processing_duration = models.DurationField(_('processing duration'), null=True, blank=True)
    
    # Error Handling
    error_message = models.TextField(_('error message'), blank=True)
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    retry_count = models.PositiveIntegerField(_('retry count'), default=0)
    max_retries = models.PositiveIntegerField(_('max retries'), default=3)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_ldt_messages')
    
    # Meta
    class Meta:
        verbose_name = _('LDT Message')
        verbose_name_plural = _('LDT Messages')
        db_table = 'ldt_messages'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['mirth_message_id']),
            models.Index(fields=['status']),
            models.Index(fields=['message_type']),
            models.Index(fields=['received_at']),
        ]
    
    def __str__(self):
        return f"{self.message_id} - {self.message_type} ({self.status})"
    
    def process_message(self):
        """Process the LDT message."""
        from django.utils import timezone
        import time
        
        start_time = time.time()
        self.status = self.Status.PROCESSING
        self.save()
        
        try:
            # Parse LDT message
            self.parsed_message = self._parse_ldt_message()
            self.message_structure = self._extract_message_structure()
            
            # Process based on message type
            if self.message_type == self.MessageType.RESULT:
                self._process_result_message()
            elif self.message_type == self.MessageType.ORDER:
                self._process_order_message()
            
            self.status = self.Status.PROCESSED
            self.processed_at = timezone.now()
            self.processing_duration = timezone.timedelta(seconds=time.time() - start_time)
            self.save()
            
            return True
            
        except Exception as e:
            self.status = self.Status.ERROR
            self.error_message = str(e)
            self.save()
            return False
    
    def _parse_ldt_message(self):
        """Parse LDT message into structured format."""
        # This would implement comprehensive LDT parsing
        # LDT format: MSH|^~\\&|SENDING_FACILITY|RECEIVING_FACILITY|20231201120000||ORU^R01|MSG001|P|2.5
        parsed = {}
        
        lines = self.raw_message.split('\n')
        for line in lines:
            if line.strip():
                segments = line.split('|')
                segment_type = segments[0] if segments else ''
                
                if segment_type == 'MSH':
                    parsed['msh'] = self._parse_msh_segment(segments)
                elif segment_type == 'PID':
                    parsed['pid'] = self._parse_pid_segment(segments)
                elif segment_type == 'ORC':
                    parsed['orc'] = self._parse_orc_segment(segments)
                elif segment_type == 'OBR':
                    parsed['obr'] = self._parse_obr_segment(segments)
                elif segment_type == 'OBX':
                    if 'obx' not in parsed:
                        parsed['obx'] = []
                    parsed['obx'].append(self._parse_obx_segment(segments))
        
        return parsed
    
    def _parse_msh_segment(self, segments):
        """Parse MSH (Message Header) segment."""
        return {
            'sending_facility': segments[3] if len(segments) > 3 else '',
            'receiving_facility': segments[4] if len(segments) > 4 else '',
            'message_datetime': segments[6] if len(segments) > 6 else '',
            'message_type': segments[8] if len(segments) > 8 else '',
            'message_control_id': segments[9] if len(segments) > 9 else '',
            'processing_id': segments[10] if len(segments) > 10 else '',
            'version_id': segments[11] if len(segments) > 11 else '',
        }
    
    def _parse_pid_segment(self, segments):
        """Parse PID (Patient Identification) segment."""
        return {
            'patient_id': segments[3] if len(segments) > 3 else '',
            'patient_name': segments[5] if len(segments) > 5 else '',
            'date_of_birth': segments[7] if len(segments) > 7 else '',
            'gender': segments[8] if len(segments) > 8 else '',
        }
    
    def _parse_orc_segment(self, segments):
        """Parse ORC (Common Order) segment."""
        return {
            'order_control': segments[1] if len(segments) > 1 else '',
            'placer_order_number': segments[2] if len(segments) > 2 else '',
            'filler_order_number': segments[3] if len(segments) > 3 else '',
            'placer_group_number': segments[4] if len(segments) > 4 else '',
        }
    
    def _parse_obr_segment(self, segments):
        """Parse OBR (Observation Request) segment."""
        return {
            'set_id': segments[1] if len(segments) > 1 else '',
            'placer_order_number': segments[2] if len(segments) > 2 else '',
            'filler_order_number': segments[3] if len(segments) > 3 else '',
            'universal_service_id': segments[4] if len(segments) > 4 else '',
            'priority': segments[5] if len(segments) > 5 else '',
            'requested_datetime': segments[6] if len(segments) > 6 else '',
            'observation_datetime': segments[7] if len(segments) > 7 else '',
            'specimen_received_datetime': segments[14] if len(segments) > 14 else '',
        }
    
    def _parse_obx_segment(self, segments):
        """Parse OBX (Observation/Result) segment."""
        return {
            'set_id': segments[1] if len(segments) > 1 else '',
            'value_type': segments[2] if len(segments) > 2 else '',
            'observation_id': segments[3] if len(segments) > 3 else '',
            'sub_id': segments[4] if len(segments) > 4 else '',
            'observation_value': segments[5] if len(segments) > 5 else '',
            'units': segments[6] if len(segments) > 6 else '',
            'reference_range': segments[7] if len(segments) > 7 else '',
            'abnormal_flags': segments[8] if len(segments) > 8 else '',
            'probability': segments[9] if len(segments) > 9 else '',
            'nature_of_abnormal_test': segments[10] if len(segments) > 10 else '',
            'observation_result_status': segments[11] if len(segments) > 11 else '',
            'effective_date_of_reference_range': segments[12] if len(segments) > 12 else '',
            'user_defined_access_checks': segments[13] if len(segments) > 13 else '',
            'observation_datetime': segments[14] if len(segments) > 14 else '',
            'producer_id': segments[15] if len(segments) > 15 else '',
            'responsible_observer': segments[16] if len(segments) > 16 else '',
        }
    
    def _extract_message_structure(self):
        """Extract message structure for analysis."""
        return {
            'total_segments': len(self.raw_message.split('\n')),
            'segment_types': list(set([line.split('|')[0] for line in self.raw_message.split('\n') if line.strip()])),
            'message_size': len(self.raw_message),
            'has_patient_data': 'PID' in self.raw_message,
            'has_order_data': 'ORC' in self.raw_message,
            'has_result_data': 'OBX' in self.raw_message,
        }
    
    def _process_result_message(self):
        """Process result message and create/update test results."""
        if 'obx' not in self.parsed_message:
            return
        
        for obx in self.parsed_message['obx']:
            # Find or create test result
            test_result, created = TestResult.objects.get_or_create(
                ldt_message_id=self.message_id,
                ldt_obx_sequence=obx.get('set_id'),
                defaults={
                    'result_id': f"{self.message_id}_{obx.get('set_id')}",
                    'test_order': self._find_test_order(obx),
                    'result_value': obx.get('observation_value', ''),
                    'result_unit': obx.get('units', ''),
                    'ldt_raw_data': obx,
                    'ldt_parsed_data': obx,
                    'ldt_processing_status': 'PROCESSED',
                }
            )
            
            if not created:
                # Update existing result
                test_result.result_value = obx.get('observation_value', '')
                test_result.ldt_raw_data = obx
                test_result.ldt_parsed_data = obx
                test_result.ldt_processing_status = 'PROCESSED'
                test_result.save()
    
    def _process_order_message(self):
        """Process order message and create test orders."""
        # Implementation for processing order messages
        pass
    
    def _find_test_order(self, obx):
        """Find corresponding test order for OBX segment."""
        # This would implement logic to find the correct test order
        # based on patient ID, test code, etc.
        return None


class ResultWorkflow(models.Model):
    """
    Result workflow management for automated processing.
    """
    
    # Workflow Type Choices
    class WorkflowType(models.TextChoices):
        AUTO_VALIDATION = 'AUTO_VALIDATION', _('Auto Validation')
        CRITICAL_VALUE_ALERT = 'CRITICAL_VALUE_ALERT', _('Critical Value Alert')
        QC_REVIEW = 'QC_REVIEW', _('QC Review')
        CLINICAL_REVIEW = 'CLINICAL_REVIEW', _('Clinical Review')
        FINAL_APPROVAL = 'FINAL_APPROVAL', _('Final Approval')
        REPORT_GENERATION = 'REPORT_GENERATION', _('Report Generation')
    
    # Status Choices
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_id = models.CharField(_('workflow ID'), max_length=50, unique=True)
    
    # Workflow Information
    workflow_type = models.CharField(_('workflow type'), max_length=30, choices=WorkflowType.choices)
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Associated Results
    results = models.ManyToManyField(TestResult, related_name='workflows')
    
    # Workflow Steps
    current_step = models.CharField(_('current step'), max_length=100, default='START')
    completed_steps = models.JSONField(_('completed steps'), default=list, blank=True)
    workflow_data = models.JSONField(_('workflow data'), default=dict, blank=True)
    
    # Execution
    started_at = models.DateTimeField(_('started at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executed_workflows')
    
    # Error Handling
    error_message = models.TextField(_('error message'), blank=True)
    retry_count = models.PositiveIntegerField(_('retry count'), default=0)
    
    # Meta
    class Meta:
        verbose_name = _('Result Workflow')
        verbose_name_plural = _('Result Workflows')
        db_table = 'result_workflows'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow_id} - {self.workflow_type} ({self.status})"
    
    def execute_workflow(self):
        """Execute the workflow."""
        from django.utils import timezone
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
        
        try:
            if self.workflow_type == self.WorkflowType.AUTO_VALIDATION:
                self._execute_auto_validation()
            elif self.workflow_type == self.WorkflowType.CRITICAL_VALUE_ALERT:
                self._execute_critical_value_alert()
            
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save()
            
        except Exception as e:
            self.status = self.Status.FAILED
            self.error_message = str(e)
            self.save()
    
    def _execute_auto_validation(self):
        """Execute auto-validation workflow."""
        for result in self.results.all():
            # Implement auto-validation logic
            if result.is_abnormal:
                result.validation_status = 'REQUIRES_REVIEW'
            else:
                result.validation_status = 'AUTO_VALIDATED'
            result.save()
    
    def _execute_critical_value_alert(self):
        """Execute critical value alert workflow."""
        for result in self.results.all():
            if result.is_critical:
                # Send critical value alert
                self._send_critical_alert(result)
    
    def _send_critical_alert(self, result):
        """Send critical value alert."""
        # Implementation for sending critical value alerts
        pass


class ResultAuditLog(models.Model):
    """
    Audit log for result changes and workflow transitions.
    """
    
    # Action Choices
    class Action(models.TextChoices):
        CREATED = 'CREATED', _('Created')
        UPDATED = 'UPDATED', _('Updated')
        DELETED = 'DELETED', _('Deleted')
        VALIDATED = 'VALIDATED', _('Validated')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        STATUS_CHANGED = 'STATUS_CHANGED', _('Status Changed')
        WORKFLOW_TRANSITION = 'WORKFLOW_TRANSITION', _('Workflow Transition')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Associated Objects
    result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    workflow = models.ForeignKey(ResultWorkflow, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    ldt_message = models.ForeignKey(LDTMessage, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    
    # Action Information
    action = models.CharField(_('action'), max_length=30, choices=Action.choices)
    action_description = models.TextField(_('action description'), blank=True)
    
    # Changes
    old_values = models.JSONField(_('old values'), default=dict, blank=True)
    new_values = models.JSONField(_('new values'), default=dict, blank=True)
    
    # User and Timestamp
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    performed_at = models.DateTimeField(_('performed at'), auto_now_add=True)
    
    # Additional Context
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    session_id = models.CharField(_('session ID'), max_length=100, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('Result Audit Log')
        verbose_name_plural = _('Result Audit Logs')
        db_table = 'result_audit_logs'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.action} by {self.performed_by} at {self.performed_at}"