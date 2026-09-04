# apps/booking/forms.py
from django import forms
from django_countries.widgets import CountrySelectWidget
from .models import Booking, GroupMember, ContactEnquiry


# Shared Tailwind-friendly widget mixin attrs
_INPUT_CLASS  = 'vk-input w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-sa-orange focus:ring-2 focus:ring-sa-orange/20 transition'
_SELECT_CLASS = 'vk-select w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-sa-orange focus:ring-2 focus:ring-sa-orange/20 transition bg-white'
_TEXTAREA_CLASS = 'vk-input w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-sa-orange focus:ring-2 focus:ring-sa-orange/20 transition resize-none'


class BookingForm(forms.ModelForm):
    """
    Individual tour booking — pure enquiry, no payment.
    WhatsApp is the default preferred contact because that's how most
    Structured Adventures clients communicate.
    """

    class Meta:
        model  = Booking
        fields = [
            'full_name', 'email', 'phone_number', 'whatsapp_number',
            'country', 'num_people', 'travel_date', 'flexible_dates',
            'experience_level', 'preferred_contact', 'message',
        ]
        widgets = {
            'full_name':        forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'Your full name',
                'autocomplete': 'name',
            }),
            'email':            forms.EmailInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'your@email.com',
                'autocomplete': 'email',
            }),
            'phone_number':     forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': '+255 700 000 000',
                'autocomplete': 'tel',
            }),
            'whatsapp_number':  forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': '+255 700 000 000 (if different from phone)',
            }),
            'country':          CountrySelectWidget(attrs={'class': _SELECT_CLASS}),
            'num_people':       forms.NumberInput(attrs={
                'class': _INPUT_CLASS,
                'min': 1, 'max': 50,
            }),
            'travel_date':      forms.DateInput(attrs={
                'class': _INPUT_CLASS,
                'type': 'date',
            }),
            'flexible_dates':   forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-slate-300 text-sa-orange focus:ring-sa-orange',
            }),
            'experience_level': forms.Select(attrs={'class': _SELECT_CLASS}),
            'preferred_contact': forms.RadioSelect(attrs={
                'class': 'sr-only',  # styled via Alpine/custom CSS
            }),
            'message':          forms.Textarea(attrs={
                'class': _TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'Tell us about your group, any special requirements, dietary needs, or questions…',
            }),
        }
        labels = {
            'whatsapp_number':  'WhatsApp Number',
            'num_people':       'Number of People',
            'travel_date':      'Preferred Start Date',
            'flexible_dates':   'I\'m flexible on the exact date',
            'experience_level': 'Your Hiking Experience',
            'preferred_contact': 'Best Way to Reach You',
            'message':          'Special Requests / Questions',
        }

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        phone = cleaned.get('phone_number')
        if not email and not phone:
            raise forms.ValidationError(
                "Please provide at least an email address or phone number so we can reach you."
            )
        return cleaned

    def clean_travel_date(self):
        from django.utils import timezone
        d = self.cleaned_data.get('travel_date')
        if d and d < timezone.now().date():
            raise forms.ValidationError("Travel date cannot be in the past.")
        return d

    def clean_num_people(self):
        n = self.cleaned_data.get('num_people', 1)
        if n < 1:
            raise forms.ValidationError("Must be at least 1 person.")
        if n > 50:
            raise forms.ValidationError("For groups over 50 people please contact us directly.")
        return n


class GroupJoinForm(forms.ModelForm):
    """
    Group departure join request — no payment, just capture client details.
    Staff review and send DPO link once confirmed.
    """

    class Meta:
        model  = GroupMember
        fields = [
            'full_name', 'email', 'phone_number', 'whatsapp_number',
            'country', 'party_size', 'message',
        ]
        widgets = {
            'full_name':        forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'Your full name',
                'autocomplete': 'name',
            }),
            'email':            forms.EmailInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'your@email.com',
                'autocomplete': 'email',
            }),
            'phone_number':     forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': '+255 700 000 000',
                'autocomplete': 'tel',
            }),
            'whatsapp_number':  forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': '+255 700 000 000 (if different from phone)',
            }),
            'country':          CountrySelectWidget(attrs={'class': _SELECT_CLASS}),
            'party_size':       forms.NumberInput(attrs={
                'class': _INPUT_CLASS,
                'min': 1, 'max': 20,
            }),
            'message':          forms.Textarea(attrs={
                'class': _TEXTAREA_CLASS,
                'rows': 3,
                'placeholder': 'Special requests, dietary needs, experience level…',
            }),
        }
        labels = {
            'party_size':       'How many people in your group?',
            'whatsapp_number':  'WhatsApp Number',
            'message':          'Special Requests / Questions',
        }

    def clean_party_size(self):
        n = self.cleaned_data.get('party_size', 1)
        if n < 1:
            raise forms.ValidationError("Party size must be at least 1.")
        return n


class ContactEnquiryForm(forms.ModelForm):
    """General contact form."""

    class Meta:
        model  = ContactEnquiry
        fields = ['name', 'email', 'phone', 'topic', 'subject', 'message']
        widgets = {
            'name':    forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'Your name',
                'autocomplete': 'name',
            }),
            'email':   forms.EmailInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'your@email.com',
                'autocomplete': 'email',
            }),
            'phone':   forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': '+255 700 000 000',
            }),
            'topic':   forms.Select(attrs={'class': _SELECT_CLASS}),
            'subject': forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'What is your enquiry about?',
            }),
            'message': forms.Textarea(attrs={
                'class': _TEXTAREA_CLASS,
                'rows': 5,
                'placeholder': 'Tell us more about your plans…',
            }),
        }
