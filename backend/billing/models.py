from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class BillingPlan(models.Model):
    """SaaS billing plans"""
    PLAN_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.PositiveIntegerField()
    max_patients = models.PositiveIntegerField()
    max_tests_per_month = models.PositiveIntegerField()
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} - {self.get_plan_type_display()}"
    
    @property
    def yearly_discount(self):
        """Calculate yearly discount percentage"""
        if self.price_monthly > 0:
            yearly_monthly = self.price_yearly / 12
            discount = ((self.price_monthly - yearly_monthly) / self.price_monthly) * 100
            return round(discount, 1)
        return 0


class Subscription(models.Model):
    """User subscriptions to billing plans"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('trial', 'Trial'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(BillingPlan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status in ['active', 'trial'] and
            self.current_period_end > now
        )
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'trial' and
            self.trial_end_date and
            self.trial_end_date > now
        )


class Invoice(models.Model):
    """Billing invoices"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('uncollectible', 'Uncollectible'),
        ('void', 'Void'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.subscription.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)
    
    def _generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"INV-{timestamp}"


class Usage(models.Model):
    """Usage tracking for billing"""
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage')
    date = models.DateField()
    users_count = models.PositiveIntegerField(default=0)
    patients_count = models.PositiveIntegerField(default=0)
    tests_count = models.PositiveIntegerField(default=0)
    storage_mb = models.PositiveIntegerField(default=0)
    api_calls = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['subscription', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.subscription} - {self.date}"
    
    @property
    def total_usage_cost(self):
        """Calculate total usage cost based on plan limits"""
        plan = self.subscription.plan
        
        # Calculate overage costs
        user_overage = max(0, self.users_count - plan.max_users)
        patient_overage = max(0, self.patients_count - plan.max_patients)
        test_overage = max(0, self.tests_count - plan.max_tests_per_month)
        
        # Overage pricing (example rates)
        user_cost = user_overage * Decimal('5.00')  # €5 per additional user
        patient_cost = patient_overage * Decimal('0.10')  # €0.10 per additional patient
        test_cost = test_overage * Decimal('0.05')  # €0.05 per additional test
        
        return user_cost + patient_cost + test_cost


class PaymentMethod(models.Model):
    """Payment methods for users"""
    PAYMENT_TYPES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('sepa_direct_debit', 'SEPA Direct Debit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)  # Store payment details securely
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_payment_type_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)