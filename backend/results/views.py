"""
API views for Results management with LDT integration.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, Avg, Min, Max
from django.http import JsonResponse
import logging
import uuid

from .models import (
    TestResult, LDTMessage, ResultStatus, ResultWorkflow, ResultAuditLog
)
from .serializers import (
    TestResultSerializer, LDTMessageSerializer, ResultStatusSerializer,
    ResultWorkflowSerializer, ResultAuditLogSerializer
)
from .permissions import (
    CanViewResults, CanEditResults, CanValidateResults, CanApproveResults
)
from .tasks import process_ldt_message_task, send_critical_alert_task

logger = logging.getLogger(__name__)


class TestResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing test results with comprehensive CRUD operations.
    """
    
    queryset = TestResult.objects.select_related(
        'test_order', 'sample', 'test', 'patient', 'status',
        'validated_by', 'approved_by', 'result_entered_by'
    ).prefetch_related('workflows', 'audit_logs')
    
    serializer_class = TestResultSerializer
    permission_classes = [IsAuthenticated, CanViewResults]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'test', 'patient', 'critical_level', 'validation_status',
        'qc_status', 'result_type', 'ldt_processing_status'
    ]
    search_fields = [
        'result_id', 'result_value', 'clinical_notes', 'interpretation'
    ]
    ordering_fields = [
        'result_date', 'created_at', 'numeric_value', 'critical_level'
    ]
    ordering = ['-result_date']
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, CanEditResults]
        elif self.action in ['validate', 'approve', 'reject']:
            self.permission_classes = [IsAuthenticated, CanValidateResults]
        elif self.action in ['final_approve']:
            self.permission_classes = [IsAuthenticated, CanApproveResults]
        
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Create result with audit logging."""
        with transaction.atomic():
            result = serializer.save(
                created_by=self.request.user,
                result_entered_by=self.request.user
            )
            
            # Log creation
            ResultAuditLog.objects.create(
                result=result,
                action=ResultAuditLog.Action.CREATED,
                performed_by=self.request.user,
                new_values=serializer.data,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )
            
            # Trigger workflow if needed
            self._trigger_workflow(result)
    
    def perform_update(self, serializer):
        """Update result with audit logging."""
        with transaction.atomic():
            old_values = TestResultSerializer(serializer.instance).data
            result = serializer.save()
            
            # Log update
            ResultAuditLog.objects.create(
                result=result,
                action=ResultAuditLog.Action.UPDATED,
                performed_by=self.request.user,
                old_values=old_values,
                new_values=serializer.data,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )
    
    def perform_destroy(self, instance):
        """Delete result with audit logging."""
        with transaction.atomic():
            old_values = TestResultSerializer(instance).data
            
            # Log deletion
            ResultAuditLog.objects.create(
                result=instance,
                action=ResultAuditLog.Action.DELETED,
                performed_by=self.request.user,
                old_values=old_values,
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )
            
            instance.delete()
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate a test result."""
        result = self.get_object()
        
        if result.validation_status != 'PENDING':
            return Response(
                {'error': 'Result is not in pending validation status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            result.validation_status = 'VALIDATED'
            result.validated_by = request.user
            result.validated_at = timezone.now()
            result.validation_notes = request.data.get('notes', '')
            result.save()
            
            # Log validation
            ResultAuditLog.objects.create(
                result=result,
                action=ResultAuditLog.Action.VALIDATED,
                performed_by=request.user,
                new_values={'validation_status': 'VALIDATED'},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Trigger next workflow step
            self._trigger_workflow(result)
        
        return Response({'status': 'Result validated successfully'})
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a test result."""
        result = self.get_object()
        
        if result.validation_status != 'VALIDATED':
            return Response(
                {'error': 'Result must be validated before approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            result.approved_by = request.user
            result.approved_at = timezone.now()
            result.approval_notes = request.data.get('notes', '')
            result.save()
            
            # Log approval
            ResultAuditLog.objects.create(
                result=result,
                action=ResultAuditLog.Action.APPROVED,
                performed_by=request.user,
                new_values={'approved_by': request.user.id, 'approved_at': timezone.now()},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            
            # Send critical alert if needed
            if result.is_critical:
                send_critical_alert_task.delay(result.id)
        
        return Response({'status': 'Result approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a test result."""
        result = self.get_object()
        
        with transaction.atomic():
            result.validation_status = 'REJECTED'
            result.validation_notes = request.data.get('notes', '')
            result.save()
            
            # Log rejection
            ResultAuditLog.objects.create(
                result=result,
                action=ResultAuditLog.Action.REJECTED,
                performed_by=request.user,
                new_values={'validation_status': 'REJECTED'},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
        
        return Response({'status': 'Result rejected successfully'})
    
    @action(detail=True, methods=['post'])
    def process_ldt(self, request, pk=None):
        """Process LDT data for a result."""
        result = self.get_object()
        ldt_data = request.data.get('ldt_data')
        
        if not ldt_data:
            return Response(
                {'error': 'LDT data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            success = result.process_ldt_data(ldt_data)
            if success:
                return Response({'status': 'LDT data processed successfully'})
            else:
                return Response(
                    {'error': 'Failed to process LDT data'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error processing LDT data: {e}")
            return Response(
                {'error': 'Error processing LDT data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def critical_results(self, request):
        """Get all critical results."""
        critical_results = self.queryset.filter(
            critical_level__in=[
                TestResult.CriticalLevel.CRITICAL_LOW,
                TestResult.CriticalLevel.CRITICAL_HIGH,
                TestResult.CriticalLevel.PANIC_LOW,
                TestResult.CriticalLevel.PANIC_HIGH,
            ]
        )
        
        page = self.paginate_queryset(critical_results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(critical_results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def abnormal_results(self, request):
        """Get all abnormal results."""
        abnormal_results = self.queryset.filter(
            Q(critical_level__in=[
                TestResult.CriticalLevel.LOW,
                TestResult.CriticalLevel.HIGH,
                TestResult.CriticalLevel.ABNORMAL,
            ]) | Q(validation_status='REQUIRES_REVIEW')
        )
        
        page = self.paginate_queryset(abnormal_results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(abnormal_results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get result statistics."""
        stats = {
            'total_results': self.queryset.count(),
            'pending_validation': self.queryset.filter(validation_status='PENDING').count(),
            'validated': self.queryset.filter(validation_status='VALIDATED').count(),
            'approved': self.queryset.filter(approved_by__isnull=False).count(),
            'critical_results': self.queryset.filter(
                critical_level__in=[
                    TestResult.CriticalLevel.CRITICAL_LOW,
                    TestResult.CriticalLevel.CRITICAL_HIGH,
                    TestResult.CriticalLevel.PANIC_LOW,
                    TestResult.CriticalLevel.PANIC_HIGH,
                ]
            ).count(),
            'abnormal_results': self.queryset.filter(
                Q(critical_level__in=[
                    TestResult.CriticalLevel.LOW,
                    TestResult.CriticalLevel.HIGH,
                    TestResult.CriticalLevel.ABNORMAL,
                ]) | Q(validation_status='REQUIRES_REVIEW')
            ).count(),
        }
        
        return Response(stats)
    
    def _trigger_workflow(self, result):
        """Trigger appropriate workflow for result."""
        try:
            if result.is_critical:
                workflow = ResultWorkflow.objects.create(
                    workflow_id=f"CRITICAL_{result.id}",
                    workflow_type=ResultWorkflow.WorkflowType.CRITICAL_VALUE_ALERT,
                    status=ResultWorkflow.Status.PENDING
                )
                workflow.results.add(result)
                workflow.execute_workflow()
            
            elif result.validation_status == 'PENDING':
                workflow = ResultWorkflow.objects.create(
                    workflow_id=f"VALIDATION_{result.id}",
                    workflow_type=ResultWorkflow.WorkflowType.AUTO_VALIDATION,
                    status=ResultWorkflow.Status.PENDING
                )
                workflow.results.add(result)
                workflow.execute_workflow()
        
        except Exception as e:
            logger.error(f"Error triggering workflow for result {result.id}: {e}")


class LDTMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing LDT messages and Mirth Connect integration.
    """
    
    queryset = LDTMessage.objects.all()
    serializer_class = LDTMessageSerializer
    permission_classes = [IsAuthenticated, CanViewResults]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'message_type', 'sending_facility']
    search_fields = ['message_id', 'mirth_message_id']
    ordering = ['-received_at']
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, CanEditResults]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Create LDT message and trigger processing."""
        with transaction.atomic():
            message = serializer.save(created_by=self.request.user)
            
            # Trigger async processing
            process_ldt_message_task.delay(message.id)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess an LDT message."""
        message = self.get_object()
        
        try:
            success = message.process_message()
            if success:
                return Response({'status': 'Message reprocessed successfully'})
            else:
                return Response(
                    {'error': 'Failed to reprocess message'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Error reprocessing LDT message: {e}")
            return Response(
                {'error': 'Error reprocessing message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry processing a failed LDT message."""
        message = self.get_object()
        
        if message.status != LDTMessage.Status.ERROR:
            return Response(
                {'error': 'Message is not in error status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if message.retry_count >= message.max_retries:
            return Response(
                {'error': 'Maximum retry count exceeded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.retry_count += 1
        message.status = LDTMessage.Status.RECEIVED
        message.error_message = ''
        message.save()
        
        # Trigger reprocessing
        process_ldt_message_task.delay(message.id)
        
        return Response({'status': 'Message queued for retry'})
    
    @action(detail=False, methods=['get'])
    def processing_stats(self, request):
        """Get LDT processing statistics."""
        stats = {
            'total_messages': self.queryset.count(),
            'received': self.queryset.filter(status=LDTMessage.Status.RECEIVED).count(),
            'processing': self.queryset.filter(status=LDTMessage.Status.PROCESSING).count(),
            'processed': self.queryset.filter(status=LDTMessage.Status.PROCESSED).count(),
            'error': self.queryset.filter(status=LDTMessage.Status.ERROR).count(),
            'rejected': self.queryset.filter(status=LDTMessage.Status.REJECTED).count(),
            'pending_review': self.queryset.filter(status=LDTMessage.Status.PENDING_REVIEW).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_process(self, request):
        """Bulk process multiple LDT messages."""
        message_ids = request.data.get('message_ids', [])
        
        if not message_ids:
            return Response(
                {'error': 'Message IDs are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = self.queryset.filter(id__in=message_ids)
        processed_count = 0
        error_count = 0
        
        for message in messages:
            try:
                success = message.process_message()
                if success:
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing message {message.id}: {e}")
        
        return Response({
            'processed': processed_count,
            'errors': error_count,
            'total': len(message_ids)
        })


class ResultStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing result statuses.
    """
    
    queryset = ResultStatus.objects.all()
    serializer_class = ResultStatusSerializer
    permission_classes = [IsAuthenticated, CanViewResults]
    filterset_fields = ['is_final', 'requires_review', 'can_edit']
    ordering = ['name']


class ResultWorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing result workflows.
    """
    
    queryset = ResultWorkflow.objects.select_related('executed_by').prefetch_related('results')
    serializer_class = ResultWorkflowSerializer
    permission_classes = [IsAuthenticated, CanViewResults]
    filterset_fields = ['workflow_type', 'status']
    ordering = ['-started_at']
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a workflow."""
        workflow = self.get_object()
        
        if workflow.status != ResultWorkflow.Status.PENDING:
            return Response(
                {'error': 'Workflow is not in pending status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            workflow.execute_workflow()
            return Response({'status': 'Workflow executed successfully'})
        except Exception as e:
            logger.error(f"Error executing workflow {workflow.id}: {e}")
            return Response(
                {'error': 'Error executing workflow'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def workflow_stats(self, request):
        """Get workflow statistics."""
        stats = {
            'total_workflows': self.queryset.count(),
            'pending': self.queryset.filter(status=ResultWorkflow.Status.PENDING).count(),
            'in_progress': self.queryset.filter(status=ResultWorkflow.Status.IN_PROGRESS).count(),
            'completed': self.queryset.filter(status=ResultWorkflow.Status.COMPLETED).count(),
            'failed': self.queryset.filter(status=ResultWorkflow.Status.FAILED).count(),
            'cancelled': self.queryset.filter(status=ResultWorkflow.Status.CANCELLED).count(),
        }
        
        return Response(stats)


class ResultAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing result audit logs.
    """
    
    queryset = ResultAuditLog.objects.select_related(
        'result', 'workflow', 'ldt_message', 'performed_by'
    )
    serializer_class = ResultAuditLogSerializer
    permission_classes = [IsAuthenticated, CanViewResults]
    filterset_fields = ['action', 'performed_by']
    ordering = ['-performed_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Filter by result if specified
        result_id = self.request.query_params.get('result_id')
        if result_id:
            queryset = queryset.filter(result_id=result_id)
        
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(performed_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(performed_at__lte=end_date)
        
        return queryset


# Additional utility views for LDT integration

def ldt_webhook(request):
    """
    Webhook endpoint for receiving LDT messages from Mirth Connect.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Extract LDT message from request
        ldt_data = request.body.decode('utf-8')
        
        # Create LDT message record
        message = LDTMessage.objects.create(
            message_id=f"LDT_{timezone.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            message_type=LDTMessage.MessageType.RESULT,
            status=LDTMessage.Status.RECEIVED,
            raw_message=ldt_data,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Trigger async processing
        process_ldt_message_task.delay(message.id)
        
        return JsonResponse({
            'status': 'success',
            'message_id': message.message_id,
            'message': 'LDT message received and queued for processing'
        })
        
    except Exception as e:
        logger.error(f"Error processing LDT webhook: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


def ldt_status(request, message_id):
    """
    Get status of LDT message processing.
    """
    try:
        message = get_object_or_404(LDTMessage, message_id=message_id)
        
        return JsonResponse({
            'message_id': message.message_id,
            'status': message.status,
            'received_at': message.received_at.isoformat(),
            'processed_at': message.processed_at.isoformat() if message.processed_at else None,
            'error_message': message.error_message,
            'retry_count': message.retry_count
        })
        
    except Exception as e:
        logger.error(f"Error getting LDT status: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)