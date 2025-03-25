from django.conf import settings
from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.models import UserManager
from users.serializers import SignUpSerializer, SignInResponseSerializer, SignInRequestSerializer


class SignUpAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user_manager = UserManager()

        user = user_manager.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name']
        )

        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(user).data,
        )


class SignInAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignInResponseSerializer

    def post(self, request):
        serializer = SignInRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        manager = UserManager()

        email = validated_data["email"]
        password = validated_data["password"]

        user, tokens = manager.get_tokens_for_user(email, password)
        if settings.SIMPLE_JWT.get("UPDATE_LAST_LOGIN", False):
            update_last_login(None, user)

        return Response(
            data=self.serializer_class(tokens).data,
            status=status.HTTP_200_OK,
        )
