from rest_framework import serializers


class SignUpSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(write_only=True)


class SignInRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)


class SignInResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    exp = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S")
