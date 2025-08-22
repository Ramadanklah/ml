"""
Celery tasks for Results management and LDT processing.
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from .models import TestResult, LDTMessage, ResultWorkflow, ResultAuditLog
from .serializers import TestResultSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_ldt_message_task(self, message_id):
    """
    Process LDT message asynchronously.
    
    Args:
        message_id: ID of the LDT message to process
    """
    try:
        with transaction.atomic():
            message = LDTMessage.objects.select_for_update().get(id=message_id)
            
            if message.status != LDTMessage.Status.RECEIVED:
                logger.warning(f"Message {message_id} is not in RECEIVED status")
                return False
            
            # Process the message
            success = message.process_message()
            
            if success:
                logger.info(f"Successfully processed LDT message {message_id}")
                return True
            else:
                logger.error(f"Failed to process LDT message {message_id}")
                return False
                
    except LDTMessage.DoesNotExist:
        logger.error(f"LDT message {message_id} not found")
        return False
    except Exception as exc:
        logger.error(f"Error processing LDT message {message_id}: {exc}")
        
        # Retry the task
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceeded:
            logger.error(f"Max retries exceeded for LDT message {message_id}")
            
            # Mark message as failed
            try:
                message = LDTMessage.objects.get(id=message_id)
                message.status = LDTMessage.Status.ERROR
                message.error_message = f"Max retries exceeded: {exc}"
                message.save()
            except LDTMessage.DoesNotExist:
                pass
            
            return False
        
        return False


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_critical_alert_task(self, result_id):
    """
    Send critical value alert for test result.
    
    Args:
        result_id: ID of the test result
    """
    try:
        with transaction.atomic():
            result = TestResult.objects.select_related(
                'patient', 'test', 'test_order'
            ).get(id=result_id)
            
            if not result.is_critical:
                logger.warning(f"Result {result_id} is not critical")
                return False
            
            # Get users who should receive critical alerts
            alert_users = get_critical_alert_recipients(result)
            
            if not alert_users:
                logger.warning(f"No users found to receive critical alert for result {result_id}")
                return False
            
            # Send alerts
            alert_sent = False
            for user in alert_users:
                try:
                    send_critical_alert_email(user, result)
                    alert_sent = True
                except Exception as e:
                    logger.error(f"Failed to send critical alert to user {user.id}: {e}")
            
            # Log alert sending
            if alert_sent:
                ResultAuditLog.objects.create(
                    result=result,
                    action=ResultAuditLog.Action.STATUS_CHANGED,
                    performed_by=None,  # System action
                    action_description=f"Critical value alert sent to {len(alert_users)} users",
                    new_values={'critical_alert_sent': True, 'alert_recipients': [u.id for u in alert_users]}
                )
                
                logger.info(f"Critical alert sent for result {result_id}")
                return True
            else:
                logger.error(f"Failed to send critical alert for result {result_id}")
                return False
                
    except TestResult.DoesNotExist:
        logger.error(f"Test result {result_id} not found")
        return False
    except Exception as exc:
        logger.error(f"Error sending critical alert for result {result_id}: {exc}")
        
        # Retry the task
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceeded:
            logger.error(f"Max retries exceeded for critical alert {result_id}")
            return False
        
        return False


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def process_result_workflow_task(self, workflow_id):
    """
    Process result workflow asynchronously.
    
    Args:
        workflow_id: ID of the workflow to process
    """
    try:
        with transaction.atomic():
            workflow = ResultWorkflow.objects.select_for_update().get(id=workflow_id)
            
            if workflow.status != ResultWorkflow.Status.PENDING:
                logger.warning(f"Workflow {workflow_id} is not in PENDING status")
                return False
            
            # Execute the workflow
            workflow.execute_workflow()
            
            logger.info(f"Successfully executed workflow {workflow_id}")
            return True
                
    except ResultWorkflow.DoesNotExist:
        logger.error(f"Workflow {workflow_id} not found")
        return False
    except Exception as exc:
        logger.error(f"Error executing workflow {workflow_id}: {exc}")
        
        # Retry the task
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceeded:
            logger.error(f"Max retries exceeded for workflow {workflow_id}")
            
            # Mark workflow as failed
            try:
                workflow = ResultWorkflow.objects.get(id=workflow_id)
                workflow.status = ResultWorkflow.Status.FAILED
                workflow.error_message = f"Max retries exceeded: {exc}"
                workflow.save()
            except ResultWorkflow.DoesNotExist:
                pass
            
            return False
        
        return False


@shared_task
def cleanup_old_ldt_messages():
    """
    Clean up old LDT messages to prevent database bloat.
    """
    try:
        # Delete messages older than 90 days that are not in error status
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        
        deleted_count = LDTMessage.objects.filter(
            created_at__lt=cutoff_date,
            status__in=[
                LDTMessage.Status.PROCESSED,
                LDTMessage.Status.REJECTED
            ]
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old LDT messages")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old LDT messages: {e}")
        return 0


@shared_task
def cleanup_old_audit_logs():
    """
    Clean up old audit logs to prevent database bloat.
    """
    try:
        # Delete audit logs older than 1 year
        cutoff_date = timezone.now() - timezone.timedelta(days=365)
        
        deleted_count = ResultAuditLog.objects.filter(
            performed_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old audit logs")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old audit logs: {e}")
        return 0


@shared_task
def validate_results_batch():
    """
    Batch validate results that meet auto-validation criteria.
    """
    try:
        with transaction.atomic():
            # Get results that can be auto-validated
            auto_validation_results = TestResult.objects.filter(
                validation_status='PENDING',
                critical_level__in=[
                    TestResult.CriticalLevel.NORMAL,
                    TestResult.CriticalLevel.NEGATIVE,
                    TestResult.CriticalLevel.NONREACTIVE
                ]
            ).select_related('test', 'patient')
            
            validated_count = 0
            for result in auto_validation_results:
                try:
                    # Auto-validate the result
                    result.validation_status = 'AUTO_VALIDATED'
                    result.validated_at = timezone.now()
                    result.validation_notes = 'Auto-validated by system'
                    result.save()
                    
                    # Log the auto-validation
                    ResultAuditLog.objects.create(
                        result=result,
                        action=ResultAuditLog.Action.VALIDATED,
                        performed_by=None,  # System action
                        action_description='Auto-validated by system',
                        new_values={'validation_status': 'AUTO_VALIDATED'}
                    )
                    
                    validated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error auto-validating result {result.id}: {e}")
                    continue
            
            logger.info(f"Auto-validated {validated_count} results")
            return validated_count
            
    except Exception as e:
        logger.error(f"Error in batch result validation: {e}")
        return 0


@shared_task
def send_daily_result_summary():
    """
    Send daily summary of test results to laboratory staff.
    """
    try:
        # Get yesterday's results
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        
        results_summary = TestResult.objects.filter(
            result_date__date=yesterday
        ).aggregate(
            total_results=Count('id'),
            pending_validation=Count('id', filter=Q(validation_status='PENDING')),
            validated=Count('id', filter=Q(validation_status='VALIDATED')),
            approved=Count('id', filter=Q(approved_by__isnull=False)),
            critical_results=Count('id', filter=Q(
                critical_level__in=[
                    TestResult.CriticalLevel.CRITICAL_LOW,
                    TestResult.CriticalLevel.CRITICAL_HIGH,
                    TestResult.CriticalLevel.PANIC_LOW,
                    TestResult.CriticalLevel.PANIC_HIGH,
                ]
            )),
            abnormal_results=Count('id', filter=Q(
                Q(critical_level__in=[
                    TestResult.CriticalLevel.LOW,
                    TestResult.CriticalLevel.HIGH,
                    TestResult.CriticalLevel.ABNORMAL,
                ]) | Q(validation_status='REQUIRES_REVIEW')
            ))
        )
        
        # Get users who should receive daily summaries
        summary_users = get_daily_summary_recipients()
        
        # Send summary emails
        for user in summary_users:
            try:
                send_daily_summary_email(user, results_summary, yesterday)
            except Exception as e:
                logger.error(f"Failed to send daily summary to user {user.id}: {e}")
        
        logger.info(f"Daily result summary sent to {len(summary_users)} users")
        return len(summary_users)
        
    except Exception as e:
        logger.error(f"Error sending daily result summary: {e}")
        return 0


@shared_task
def monitor_ldt_processing():
    """
    Monitor LDT processing and alert on issues.
    """
    try:
        # Check for stuck messages (processing for more than 10 minutes)
        stuck_threshold = timezone.now() - timezone.timedelta(minutes=10)
        stuck_messages = LDTMessage.objects.filter(
            status=LDTMessage.Status.PROCESSING,
            updated_at__lt=stuck_threshold
        )
        
        if stuck_messages.exists():
            logger.warning(f"Found {stuck_messages.count()} stuck LDT messages")
            
            # Alert administrators
            alert_users = get_ldt_monitoring_recipients()
            for user in alert_users:
                try:
                    send_ldt_monitoring_alert(user, stuck_messages)
                except Exception as e:
                    logger.error(f"Failed to send LDT monitoring alert to user {user.id}: {e}")
        
        # Check for high error rates
        error_threshold = timezone.now() - timezone.timedelta(hours=1)
        recent_errors = LDTMessage.objects.filter(
            status=LDTMessage.Status.ERROR,
            updated_at__gte=error_threshold
        ).count()
        
        if recent_errors > 10:  # More than 10 errors in the last hour
            logger.warning(f"High LDT error rate: {recent_errors} errors in the last hour")
            
            # Alert administrators
            alert_users = get_ldt_monitoring_recipients()
            for user in alert_users:
                try:
                    send_ldt_error_rate_alert(user, recent_errors)
                except Exception as e:
                    logger.error(f"Failed to send LDT error rate alert to user {user.id}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in LDT monitoring: {e}")
        return False


# Helper functions

def get_critical_alert_recipients(result):
    """
    Get users who should receive critical value alerts.
    """
    recipients = []
    
    # Add laboratory managers
    recipients.extend(
        User.objects.filter(user_type=User.UserType.LAB_MANAGER, status=User.Status.ACTIVE)
    )
    
    # Add pathologists
    recipients.extend(
        User.objects.filter(user_type=User.UserType.PATHOLOGIST, status=User.Status.ACTIVE)
    )
    
    # Add medical technologists on duty
    recipients.extend(
        User.objects.filter(
            user_type=User.UserType.MEDICAL_TECHNOLOGIST,
            status=User.Status.ACTIVE
        )
    )
    
    # Remove duplicates
    unique_recipients = list({user.id: user for user in recipients}.values())
    
    return unique_recipients


def get_daily_summary_recipients():
    """
    Get users who should receive daily result summaries.
    """
    return User.objects.filter(
        user_type__in=[
            User.UserType.LAB_MANAGER,
            User.UserType.PATHOLOGIST,
            User.UserType.MEDICAL_TECHNOLOGIST
        ],
        status=User.Status.ACTIVE
    )


def get_ldt_monitoring_recipients():
    """
    Get users who should receive LDT monitoring alerts.
    """
    return User.objects.filter(
        user_type__in=[
            User.UserType.ADMINISTRATOR,
            User.UserType.LAB_MANAGER
        ],
        status=User.Status.ACTIVE
    )


def send_critical_alert_email(user, result):
    """
    Send critical value alert email to user.
    """
    subject = f"CRITICAL VALUE ALERT - {result.test.test_name}"
    
    message = f"""
Critical Value Alert

Test: {result.test.test_name}
Patient: {result.patient.get_full_name()} (ID: {result.patient.patient_id})
Result: {result.result_value} {result.result_unit}
Critical Level: {result.critical_level}
Reference Range: {result.reference_range_display}
Result Date: {result.result_date}

This result requires immediate attention.

Please review and take appropriate action.

---
LIS System
{settings.SITE_NAME or 'Laboratory Information System'}
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )


def send_daily_summary_email(user, summary, date):
    """
    Send daily result summary email to user.
    """
    subject = f"Daily Result Summary - {date}"
    
    message = f"""
Daily Result Summary for {date}

Total Results: {summary['total_results']}
Pending Validation: {summary['pending_validation']}
Validated: {summary['validated']}
Approved: {summary['approved']}
Critical Results: {summary['critical_results']}
Abnormal Results: {summary['abnormal_results']}

---
LIS System
{settings.SITE_NAME or 'Laboratory Information System'}
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )


def send_ldt_monitoring_alert(user, stuck_messages):
    """
    Send LDT monitoring alert for stuck messages.
    """
    subject = "LDT Monitoring Alert - Stuck Messages"
    
    message = f"""
LDT Monitoring Alert

Found {stuck_messages.count()} stuck LDT messages that have been processing for more than 10 minutes.

Please investigate the LDT processing system.

---
LIS System
{settings.SITE_NAME or 'Laboratory Information System'}
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )


def send_ldt_error_rate_alert(user, error_count):
    """
    Send LDT monitoring alert for high error rates.
    """
    subject = "LDT Monitoring Alert - High Error Rate"
    
    message = f"""
LDT Monitoring Alert

High LDT error rate detected: {error_count} errors in the last hour.

Please investigate the LDT processing system.

---
LIS System
{settings.SITE_NAME or 'Laboratory Information System'}
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )