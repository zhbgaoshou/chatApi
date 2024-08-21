from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from user.serializers import UserSerializer
from django.contrib.auth.models import User


class RegisterView(GenericAPIView):
    permission_classes = ()
    serializer_class = UserSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetPasswordView(GenericAPIView):
    def post(self, request):
        user = request.user
        password = request.data.get("password")
        password_confirmation = request.data.get("password_confirmation")
        if password != password_confirmation:
            return Response(
                {"message": "密码不一致"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            user.set_password(password)
            user.save()
            return Response({"message": "修改成功"}, status=status.HTTP_200_OK)


class UserInfoView(RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class DestroyView(GenericAPIView):
    def patch(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response({"message": "注销成功"}, status=status.HTTP_200_OK)
