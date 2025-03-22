from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from reservations.exceptions import ReservationPeriodException, ReservationAttendeesException, \
    ReservationAccessDeniedException, ReservationNotFoundException, ConfirmedReservationModificationException
from reservations.models import Reservation


class ReservationManager:
    @transaction.atomic
    def retrieve_reservations_by_user(self, user):
        """
        사용자의 권한에 따라 예약 조회

        Args:
            user: 요청 사용자 객체

        Returns:
            QuerySet[Reservation]: 예약 객체들의 QuerySet

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
            ReservationPeriodException:
                - 예약일이 시험 시작 3일 이내인 경우
                - 종료 시간이 시작 시작보다 앞서거나 같은 경우
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

    @transaction.atomic
    def retrieve_reservation_by_id(self, user, reservation_id):
        """
        ID로 예약 조회

        Args:
            user: 요청 사용자 객체
            reservation_id: 조회할 예약 ID

        Returns:
            QuerySet[Reservation]: 예약 객체의 QuerySet

        Raises:
            ReservationNotFoundException: 예약이 존재하지 않는 경우
            ReservationAccessDeniedException: 사용자가 해당 예약에 접근 권한이 없는 경우
        """
        try:
            # ID로 예약 조회
            reservation_qs = Reservation.objects.select_related('company_customer').get(id=reservation_id)

            if user.role == 'ADMIN' or (user.role == 'COMPANY' and reservation_qs.company_customer == user):
                return reservation_qs
            else:
                raise ReservationAccessDeniedException()
        except Reservation.DoesNotExist:
            raise ReservationNotFoundException()

    @transaction.atomic
    def update_reservation(self, reservation, user, exam_date=None, start_time=None, end_time=None, attendees=None, status=None):
        """
        사용자의 권한에 따라 예약을 수정

        Args:
            reservation: 예약
            user: 요청한 사용자
            exam_date: 예약 날짜
            start_time: 시작 시간
            end_time: 종료 시간
            attendees: 응시 인원
            status: 상태 (어드민 유저만 수정 가능)

        Returns:
            수정된 Reservation 객체

        Raises:
            ConfirmedReservationModificationException:
                기업 사용자가 확정된 예약 수정을 시도하는 경우
            ReservationAccessDeniedException:
                어드민 사용자가 아닌 다른 사용자가 status를 수정 시도할 경우
            ReservationNotFoundException:
                조회를 시도한 예약이 없는 경우
            ReservationPeriodException:
                - 예약일이 시험 시작 3일 이내인 경우
                - 종료 시간이 시작 시간보다 앞서거나 같은 경우
            ReservationAttendeesException:
                해당 시간 응시 인원이 5만명을 넘어갈 경우
        """
        # 기업 사용자가 확정된 예약을 수정하려 시도하는 경우
        if user.role != 'ADMIN' and reservation.status == 'CONFIRMED':
            raise ConfirmedReservationModificationException()

        # 필드 수정 여부 확인
        modified = False

        # 시험 날짜 수정
        if exam_date is not None:
            if exam_date <= timezone.now().date() + timedelta(days=3):
                raise ReservationPeriodException('예약은 시험 시작 3일 전까지 신청 가능합니다.')
            reservation.exam_date = exam_date
            modified = True

        # 시간 수정
        if start_time is not None:
            reservation.start_time = start_time
            modified = True

        if end_time is not None:
            reservation.end_time = end_time
            modified = True

        # 시작/종료 시간 비교 검증
        if reservation.start_time >= reservation.end_time:
            raise ReservationPeriodException('종료 시간은 시작 시간보다 늦어야합니다.')

        # 응시 인원 수정
        if attendees is not None:
            reservation.attendees = attendees
            modified = True

        # 상태 수정 (어드민 사용자만 가능)
        if status is not None:
            if user.role != 'ADMIN':
                raise ReservationAccessDeniedException("상태 수정은 어드민 사용자만 가능합니다.")
            reservation.status = status
            modified = True

        # 변경된 날짜, 시간, 인원에 대한 가능 여부 검증
        if (exam_date is not None or start_time is not None or end_time is not None or attendees is not None or
                (status is not None and status == 'CONFIRMED' and reservation.status != 'CONFIRMED')):

            other_confirmed_attendees = Reservation.objects.filter(
                status='CONFIRMED',
                exam_date=exam_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(id=reservation.id).aggregate(Sum('attendees'))['attendees__sum'] or 0

            # 최대 인원 및 남은 인원 계산
            max_attendees = 50000
            remain_attendees = max_attendees - other_confirmed_attendees

            if reservation.attendees > remain_attendees:
                raise ReservationAttendeesException(f'동 시간대 최대 5만명 까지 예약할 수 있습니다.')

        if modified is True:
            reservation.save()

        return reservation
