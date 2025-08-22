"""
Custom User model for LIS system with role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """
    Custom User model for LIS system with laboratory-specific fields.
    """
    
    # User Types
    class UserType(models.TextChoices):
        ADMINISTRATOR = 'ADMIN', _('Administrator')
        LAB_MANAGER = 'LAB_MANAGER', _('Laboratory Manager')
        MEDICAL_TECHNOLOGIST = 'MED_TECH', _('Medical Technologist')
        PHLEBOTOMIST = 'PHLEBOTOMIST', _('Phlebotomist')
        PATHOLOGIST = 'PATHOLOGIST', _('Pathologist')
        CLINICIAN = 'CLINICIAN', _('Clinician')
        RECEPTIONIST = 'RECEPTIONIST', _('Receptionist')
        VIEWER = 'VIEWER', _('Viewer')
    
    # Status Choices
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        PENDING = 'PENDING', _('Pending')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.VIEWER,
        verbose_name=_('User Type')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status')
    )
    
    # Personal Information
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    middle_name = models.CharField(_('middle name'), max_length=150, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact = models.CharField(_('emergency contact'), max_length=255, blank=True)
    
    # Professional Information
    employee_id = models.CharField(_('employee ID'), max_length=50, unique=True, blank=True)
    department = models.CharField(_('department'), max_length=100, blank=True)
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name=_('Supervisor')
    )
    
    # Laboratory Specific
    license_number = models.CharField(_('license number'), max_length=100, blank=True)
    certification_expiry = models.DateField(_('certification expiry'), null=True, blank=True)
    specialties = models.JSONField(_('specialties'), default=list, blank=True)
    
    # Security & Compliance
    last_password_change = models.DateTimeField(_('last password change'), null=True, blank=True)
    password_expiry_date = models.DateTimeField(_('password expiry date'), null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(_('failed login attempts'), default=0)
    account_locked_until = models.DateTimeField(_('account locked until'), null=True, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name=_('Created By')
    )
    
    # Preferences
    timezone = models.CharField(_('timezone'), max_length=50, default='UTC')
    language = models.CharField(_('language'), max_length=10, default='en')
    notification_preferences = models.JSONField(_('notification preferences'), default=dict, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['status']),
            models.Index(fields=['department']),
            models.Index(fields=['employee_id']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        if self.middle_name:
            full_name = f"{self.first_name} {self.middle_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    @property
    def is_laboratory_staff(self):
        """Check if user is laboratory staff."""
        return self.user_type in [
            self.UserType.LAB_MANAGER,
            self.UserType.MEDICAL_TECHNOLOGIST,
            self.UserType.PHLEBOTOMIST,
            self.UserType.PATHOLOGIST,
        ]
    
    @property
    def is_medical_staff(self):
        """Check if user is medical staff."""
        return self.user_type in [
            self.UserType.PATHOLOGIST,
            self.UserType.CLINICIAN,
        ]
    
    @property
    def can_approve_results(self):
        """Check if user can approve test results."""
        return self.user_type in [
            self.UserType.PATHOLOGIST,
            self.UserType.LAB_MANAGER,
        ]
    
    @property
    def can_manage_samples(self):
        """Check if user can manage samples."""
        return self.user_type in [
            self.UserType.LAB_MANAGER,
            self.UserType.MEDICAL_TECHNOLOGIST,
            self.UserType.PHLEBOTOMIST,
            self.UserType.RECEPTIONIST,
        ]
    
    def lock_account(self, duration_minutes=30):
        """Lock the user account for a specified duration."""
        from django.utils import timezone
        from datetime import timedelta
        
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock the user account."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock account if threshold reached."""
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= 5:
            self.lock_account()
        
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_attempts(self):
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])


class UserProfile(models.Model):
    """
    Extended user profile with additional laboratory-specific information.
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Professional Details
    title = models.CharField(_('professional title'), max_length=100, blank=True)
    qualifications = models.JSONField(_('qualifications'), default=list, blank=True)
    experience_years = models.PositiveIntegerField(_('years of experience'), null=True, blank=True)
    
    # Laboratory Assignments
    assigned_laboratories = models.JSONField(_('assigned laboratories'), default=list, blank=True)
    primary_laboratory = models.CharField(_('primary laboratory'), max_length=100, blank=True)
    
    # Skills & Competencies
    technical_skills = models.JSONField(_('technical skills'), default=list, blank=True)
    equipment_certifications = models.JSONField(_('equipment certifications'), default=list, blank=True)
    
    # Schedule & Availability
    work_schedule = models.JSONField(_('work schedule'), default=dict, blank=True)
    availability_status = models.CharField(_('availability status'), max_length=20, default='AVAILABLE')
    
    # Training & Development
    training_records = models.JSONField(_('training records'), default=list, blank=True)
    continuing_education = models.JSONField(_('continuing education'), default=list, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(_('emergency contact name'), max_length=255, blank=True)
    emergency_contact_phone = models.CharField(_('emergency contact phone'), max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(_('emergency contact relationship'), max_length=100, blank=True)
    
    # Meta
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"
    
    def get_skill_level(self, skill_name):
        """Get the proficiency level for a specific skill."""
        for skill in self.technical_skills:
            if skill.get('name') == skill_name:
                return skill.get('level', 'NOVICE')
        return None
    
    def add_qualification(self, qualification):
        """Add a new qualification to the user's profile."""
        if qualification not in self.qualifications:
            self.qualifications.append(qualification)
            self.save(update_fields=['qualifications'])


class UserSession(models.Model):
    """
    Track user sessions for security and audit purposes.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(_('session key'), max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    login_time = models.DateTimeField(_('login time'), auto_now_add=True)
    logout_time = models.DateTimeField(_('logout time'), null=True, blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Meta
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        db_table = 'user_sessions'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"Session for {self.user.email} at {self.login_time}"
    
    def end_session(self):
        """End the current session."""
        from django.utils import timezone
        
        self.logout_time = timezone.now()
        self.is_active = False
        self.save(update_fields=['logout_time', 'is_active'])