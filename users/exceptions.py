from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidSignInInfo(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "로그인 정보가 올바르지 않습니다."
    default_code = "invalid_sign_in_info"


class InvalidCredentials(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "아이디와 패스워드가 일치하지 않습니다."
    default_code = "invalid_credentials"
