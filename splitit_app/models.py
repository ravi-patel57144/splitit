from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.validators import MinValueValidator

class Occasion(models.Model):
    """Model for grouping related events/expenses"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_occasions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class Event(models.Model):
    """Model for expense events that can be grouped under occasions"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    occasion = models.ForeignKey(Occasion, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class Expenditure(models.Model):
    """Model for individual expenses within an event"""
    SPLIT_TYPE_CHOICES = [
        ('equal', 'Equal Split'),
        ('custom', 'Custom Split'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='expenditures')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.CharField(max_length=200)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenditures')
    split_type = models.CharField(max_length=10, choices=SPLIT_TYPE_CHOICES, default='equal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"

class ExpenditureSplit(models.Model):
    """Model for tracking how an expenditure is split among users"""
    expenditure = models.ForeignKey(Expenditure, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenditure_splits')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['expenditure', 'user']
    
    def __str__(self):
        return f"{self.user.username} owes ${self.amount} for {self.expenditure.description}"

class Payment(models.Model):
    """Model for tracking payments between users"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_payments')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optional link to a specific expenditure split that this payment settles
    expenditure_split = models.OneToOneField(
        ExpenditureSplit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} pays ${self.amount} to {self.to_user.username}"