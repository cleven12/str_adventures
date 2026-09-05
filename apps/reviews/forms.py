from django import forms
from .models import TourReview

class TourReviewForm(forms.ModelForm):
    class Meta:
        model = TourReview
        fields = ['rating', 'title', 'body', 'travel_date']
        widgets = {
            'travel_date': forms.DateInput(attrs={'type': 'date'}),
            'body': forms.Textarea(attrs={'rows': 4}),
        }
