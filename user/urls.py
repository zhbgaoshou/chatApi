from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from . import views

urlpatterns = [
    path('login', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify', TokenVerifyView.as_view(), name='token_verify'),
    path('register', views.RegisterView.as_view(), name='register'),
    path('info', views.UserInfoView.as_view(), name='info'),
    path('destroy', views.DestroyView.as_view(), name='destroy'),
    path('set-password', views.SetPasswordView.as_view(), name='set_password'),
    path('toggle-room', views.ToggleRoomView.as_view(), name='toggle_room')
]
