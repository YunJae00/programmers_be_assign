from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from reservations.constants import OPERATION_END_TIME, OPERATION_START_TIME, RESERVATION_MIN_DAYS_BEFORE, \
    MAX_ATTENDEES_PER_TIMESLOT
from reservations.exceptions import ReservationPeriodException


class ReservationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    company_customer = serializers.CharField(read_only=True, source='company_customer.name')
    exam_date = serializers.DateField(read_only=True)
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    attendees = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)


class ReservationRequestSerializer(serializers.Serializer):
    exam_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    attendees = serializers.IntegerField()
    status = serializers.CharField(required=False)

    def validate(self, data):
        # 날짜 검증 추가
        if 'exam_date' in data:
            if data['exam_date'] <= timezone.now().date() + timedelta(days=RESERVATION_MIN_DAYS_BEFORE):
                raise ReservationPeriodException(f'예약은 시험 시작 {RESERVATION_MIN_DAYS_BEFORE}일 전까지 신청 가능합니다.')

        # 시작 시간 영업 시간 검증
        if 'start_time' in data and data['start_time'] < OPERATION_START_TIME:
            raise ReservationPeriodException(f'시작 시간은 영업 시작 시간({OPERATION_START_TIME.isoformat()}) 이후여야 합니다.')

        # 종료 시간 영업 시간 검증
        if 'end_time' in data and data['end_time'] > OPERATION_END_TIME:
            raise ReservationPeriodException(f'종료 시간은 영업 종료 시간({OPERATION_END_TIME.isoformat()}) 이전이어야 합니다.')

        # 시작/종료 시간 비교 검증 (둘 다 있을 경우에만)
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise ReservationPeriodException('종료 시간은 시작 시간보다 늦어야합니다.')

        # 응시 인원 검증
        if 'attendees' in data:
            if data['attendees'] < 1 or data['attendees'] > MAX_ATTENDEES_PER_TIMESLOT:
                raise ReservationPeriodException(f'응시 인원은 1명에서 {MAX_ATTENDEES_PER_TIMESLOT}명 사이여야 합니다.')

        return data


class ReservationAvailableTimeResponseSerializer(serializers.Serializer):
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    available = serializers.IntegerField(read_only=True)
