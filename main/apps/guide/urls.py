from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'guide'

urlpatterns = [
    path('trekking-guides/',        views.guide_list,      name='guide_list'),
    path('articles/',               views.article_list,    name='article_list'),
    path('articles/<slug:slug>/',   views.article_detail,  name='article_detail'),
    path('blog/',                   RedirectView.as_view(pattern_name='guide:article_list', permanent=True), name='legacy_blog_list'),
    path('blog/<slug:slug>/',       RedirectView.as_view(pattern_name='guide:article_detail', permanent=True), name='legacy_blog_detail'),
    path('category/<slug:slug>/',   views.category_guides, name='category'),
    path('<slug:slug>/',            views.guide_detail,    name='detail'),
]
