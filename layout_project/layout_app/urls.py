from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('augment-layout/', views.augment_layout, name='augment_layout'),
]


