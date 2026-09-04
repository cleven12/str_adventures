from django.urls import path
from . import views

app_name = 'tours'

urlpatterns = [
    path('',                            views.tour_list,              name='tour_list'),
    path('search/',                     views.search,                 name='search'),
    path('combos/',                     views.combo_list,             name='combo_list'),
    path('combos/<slug:slug>/',         views.combo_detail,           name='combo_detail'),
    path('category/',                   views.category_list,            name='category_list'),
    path('category/<slug:slug>/',       views.category_page,          name='category_page'),
    path('tag/<slug:slug>/',            views.tag_page,               name='tag_page'),
    path('<slug:slug>/',                views.tour_detail,            name='tour_detail'),
    path('<slug:tour_slug>/departures/',views.group_departure_check,  name='group_departure_check'),
]
