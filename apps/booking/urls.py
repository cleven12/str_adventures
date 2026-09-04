# apps/booking/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # ── Individual tour bookings ────────────────────────────────────────────
    path('<slug:tour_slug>/book/',
         views.booking_create,         name='booking_create'),

    path('received/<str:booking_ref>/<str:secure_token>/',
         views.booking_received,        name='booking_received'),

    path('status/<str:booking_ref>/<str:secure_token>/',
         views.booking_confirm,         name='booking_confirm'),

    path('cancel/<str:booking_ref>/<str:secure_token>/',
         views.booking_cancel,          name='booking_cancel'),

    # ── Group departures ────────────────────────────────────────────────────
    path('groups/',
         views.group_list,              name='group_list'),

    path('groups/<slug:slug>/',
         views.group_detail,            name='group_detail'),

    path('groups/<slug:slug>/join/',
         views.group_join,              name='group_join'),

    path('groups/received/<str:member_id>/<str:secure_token>/',
         views.group_join_received,     name='group_join_received'),

    path('groups/status/<str:member_id>/<str:secure_token>/',
         views.group_join_status,       name='group_join_status'),

    # ── Contact ─────────────────────────────────────────────────────────────
    path('contact/', views.contact,     name='contact'),
]
