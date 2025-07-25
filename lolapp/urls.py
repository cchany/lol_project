from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('search/', views.search, name='search'),
    path('rank/', views.rank, name='rank'),
    path('upload/', views.upload, name='upload'),
]
