from rest_framework import serializers


class SignInReqSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)


class SignInResSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    exp = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S")
