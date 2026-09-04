# apps/itinerary/models.py
# Skeleton — AI-powered builder will be completed later
# Connects to tours.Tour M2M, saves user-generated itineraries

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomItinerary(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('saved',    'Saved'),
        ('booked',   'Booked'),
        ('expired',  'Expired'),
    ]

    user        = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='custom_itineraries'
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    title       = models.CharField(max_length=200, blank=True)
    tours       = models.ManyToManyField(
        'tours.Tour', blank=True, related_name='custom_itineraries'
    )
    total_days  = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    notes       = models.TextField(blank=True)
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    # Future: store full AI-generated plan as JSON
    ai_plan     = models.JSONField(
        default=dict, blank=True,
        help_text="Full AI-generated day-by-day plan stored as JSON"
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'custom_itineraries'
        ordering            = ['-updated_at']
        verbose_name        = 'Custom Itinerary'
        verbose_name_plural = 'Custom Itineraries'

    def __str__(self):
        owner = self.user or f"anon:{self.session_key[:8]}"
        return f"{self.title or 'Untitled'} — {owner}"
