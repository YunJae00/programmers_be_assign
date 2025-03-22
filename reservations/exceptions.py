from rest_framework import status
from rest_framework.exceptions import APIException


class ReservationPeriodException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "예약 기간을 확인해주세요."


class ReservationAttendeesException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "예약 인원을 확인해주세요."


class ReservationNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "해당 예약을 찾을 수 없습니다."


class ReservationAccessDeniedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "해당 예약에 접근할 권한이 없습니다."
