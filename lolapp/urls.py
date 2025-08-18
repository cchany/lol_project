from django.urls import path
from . import views
from .views import edit_game

urlpatterns = [
    path('', views.main, name='main'),
    path('search/', views.search, name='search'),
    path('rank/', views.rank, name='rank'),
    path('upload/', views.upload, name='upload'),
    path('database/', views.database, name='database'),
]

urlpatterns += [
    path('edit_game/<int:game_id>/', edit_game, name='edit_game'),
]
