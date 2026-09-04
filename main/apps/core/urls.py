# apps/core/urls.py — Structured Adventures
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('',           views.HomeView.as_view(), name='home'),
    path('about/',     views.about,              name='about'),
    path('contact/',   views.contact,            name='contact'),
    path('faq/',       views.faq,                name='faq'),
    path('careers/',   views.careers,            name='careers'),
    path('careers/<slug:job_slug>/apply/', views.job_apply, name='job_apply'),
    path('privacy/',   views.privacy,            name='privacy'),
    path('terms/',     views.terms,              name='terms'),
    path('currency/<str:currency_code>/', views.switch_currency, name='switch_currency'),
]
