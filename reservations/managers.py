from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from reservations.exceptions import ReservationPeriodException, ReservationAttendeesException
from reservations.models import Reservation


class ReservationManager:
    @transaction.atomic
    def retrieve_reservations_by_user(self, user):
        """
        사용자의 권한에 따라 예약 조회

        Args:
            user: 요청 사용자 객체

        Returns:
            reservations: 예약 객체

        Raises:
        """
        if user.role == 'ADMIN':
            return Reservation.objects.all().select_related('company_customer').order_by('-exam_date', 'start_time')
        elif user.role == 'COMPANY':
            return Reservation.objects.filter(company_customer=user).select_related('company_customer').order_by('-exam_date', 'start_time')

        return Reservation.objects.none()

    @transaction.atomic
    def create_reservation(self, user, exam_date, start_time, end_time, attendees):
        """
        예약 생성

        Arg:
            user: 요청한 기업 사용자
            exam_date: 시험 날짜
            start_time: 시작 시간
            end_time: 종료 시간
            attendees: 응시 인원

        Returns:
            reservation: 생성된 예약 객체

        Raises:
            ReservationPeriodException: 예약일이 시험 시작 3일 이내인 경우, 시작 종료 시간 순서가 틀린 경우
            ReservationAttendeesException: 예약 시도 인원이 5만명을 초과하는 경우
        """
        if exam_date <= timezone.now().date() + timedelta(days=3):
            raise ReservationPeriodException('예약은 시험 시작 3일 전까지 신청 가능합니다.')

        if start_time >= end_time:
            raise ReservationPeriodException('종료 시간은 시작 시간보다 늦어야합니다.')

        confirmed_attendees = Reservation.objects.filter(
            status='CONFIRMED',
            exam_date=exam_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).aggregate(Sum('attendees'))['attendees__sum'] or 0

        # 최대 응시 인원
        max_attendees = 50000
        remain_attendees = max_attendees - confirmed_attendees

        if attendees > remain_attendees:
            # 커스텀 예외 처리
            raise ReservationAttendeesException(f'동 시간대 최대 5만명 까지 예약할 수 있습니다.')

        reservation = Reservation.objects.create(
            company_customer=user,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            status='PENDING'
        )

        return reservation
