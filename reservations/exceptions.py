from rest_framework import status
from rest_framework.exceptions import APIException


class ReservationPeriodException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "예약 기간을 확인해주세요."


class ReservationAttendeesException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "예약 인원을 확인해주세요."
