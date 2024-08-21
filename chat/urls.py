from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('room', views.RoomView, basename='room')
router.register('message', views.MessageView, basename='message')

urlpatterns = [
    path("index", views.ChatView.as_view(), name="chat"),
] + router.urls
