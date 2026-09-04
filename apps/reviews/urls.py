from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.reviews_list, name='reviews_list'),
    path('submit/<slug:tour_slug>/', views.submit_review, name='submit_review'),
]
