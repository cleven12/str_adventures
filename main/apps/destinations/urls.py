from django.urls import path
from . import views

app_name = 'destinations'

urlpatterns = [
    path('', views.destination_list, name='list'),
    path('<slug:slug>/', views.destination_detail, name='detail'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
]
