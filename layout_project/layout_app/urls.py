from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('submit_rating/', views.submit_rating, name='submit_rating'),
]
