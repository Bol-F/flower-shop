from django.urls import path
from . import views
from .assistant_views import AssistantCapabilitiesView, FlowerAdviceView

urlpatterns = [
    path(
        'assistant/capabilities/',
        AssistantCapabilitiesView.as_view(),
        name='assistant-capabilities',
    ),
    path('assistant/', FlowerAdviceView.as_view(), name='flower-advice'),
    path('send/', views.SendMessageView.as_view(), name='contact-send'),
    path('my-messages/', views.MyMessagesView.as_view(), name='contact-my-list'),
    path('admin/messages/', views.AdminMessageListView.as_view(), name='contact-admin-list'),
    path(
        'admin/messages/<int:pk>/',
        views.AdminMessageDetailView.as_view(),
        name='contact-admin-detail',
    ),
    path(
        'admin/messages/<int:pk>/reply/', views.AdminReplyView.as_view(), name='contact-admin-reply'
    ),
]
