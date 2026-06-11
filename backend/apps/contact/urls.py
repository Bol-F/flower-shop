from django.urls import path
from . import views

urlpatterns = [
    path('send/', views.SendMessageView.as_view(), name='contact-send'),
    path('admin/messages/', views.AdminMessageListView.as_view(), name='contact-admin-list'),
    path('admin/messages/<int:pk>/', views.AdminMessageDetailView.as_view(), name='contact-admin-detail'),
]
