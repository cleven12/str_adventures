# apps/core/forms.py
from django import forms
from .models import JobApplication

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['name', 'email', 'phone', 'cover_letter', 'cv']
        widgets = {
            'name':         forms.TextInput(attrs={'class': 'sa-input', 'placeholder': 'Your full name'}),
            'email':        forms.EmailInput(attrs={'class': 'sa-input', 'placeholder': 'your@email.com'}),
            'phone':        forms.TextInput(attrs={'class': 'sa-input', 'placeholder': '+255 700 000 000'}),
            'cover_letter': forms.Textarea(attrs={'class': 'sa-input', 'rows': 5, 'placeholder': 'Tell us about yourself and why you want to join Structured Adventures…'}),
        }
