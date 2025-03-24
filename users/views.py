from django.conf import settings
from django.contrib.auth.models import update_last_login
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.models import UserManager
from users.serializers import SignInResSerializer, SignInReqSerializer


class SignInAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignInReqSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        manager = UserManager()

        email = validated_data["email"]
        password = validated_data["password"]

        user, tokens = manager.get_tokens_for_user(email, password)
        if settings.SIMPLE_JWT.get("UPDATE_LAST_LOGIN", False):
            update_last_login(None, user)

        return Response(
            data=SignInResSerializer(tokens).data,
            status=status.HTTP_200_OK,
        )
