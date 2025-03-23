from datetime import time

from django.db import transaction

from reservations.constants import OPERATION_START_TIME, OPERATION_END_TIME, \
    MAX_ATTENDEES_PER_TIMESLOT
from reservations.exceptions import ReservationAttendeesException, \
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
            ReservationAttendeesException: 예약 시도 인원이 예약 가능 인원을 초과하는 경우
        """
        # 시험 날짜, 시작 시간, 종료 시간에 예약 가능한 최대 응시 인원
        available_attendees = self._check_available_attendees(exam_date, start_time, end_time)

        if attendees > available_attendees:
            raise ReservationAttendeesException(f'동 시간대 최대 {MAX_ATTENDEES_PER_TIMESLOT}명 까지 예약할 수 있습니다. (현재 예약 가능 인원: {available_attendees}명)')

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
                어드민이 아닌 다른 사용자가 status를 수정 시도할 경우
            ReservationAttendeesException:
                해당 시간 응시 인원이 5만명을 넘어갈 경우
        """
        # 어드민이 아닌 사용자가 확정된 예약을 수정하려 시도하는 경우
        if user.role != 'ADMIN' and reservation.status == 'CONFIRMED':
            raise ConfirmedReservationModificationException()

        # 필드 수정 여부 확인
        modified = False

        # 시험 날짜 수정
        if exam_date is not None:
            reservation.exam_date = exam_date
            modified = True

        # 시간 수정
        if start_time is not None:
            reservation.start_time = start_time
            modified = True

        if end_time is not None:
            reservation.end_time = end_time
            modified = True

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

            # 실제 사용할 값 결정
            check_exam_date = exam_date if exam_date is not None else reservation.exam_date
            check_start_time = start_time if start_time is not None else reservation.start_time
            check_end_time = end_time if end_time is not None else reservation.end_time
            check_attendees = attendees if attendees is not None else reservation.attendees

            # 시험 날짜, 시작 시간, 종료 시간에 예약 가능한 최대 응시 인원
            available_attendees = self._check_available_attendees(check_exam_date, check_start_time, check_end_time)

            if check_attendees > available_attendees:
                raise ReservationAttendeesException(f'동 시간대 최대 {MAX_ATTENDEES_PER_TIMESLOT}명 까지 예약할 수 있습니다. (현재 예약 가능 인원: {available_attendees}명)')

        if modified is True:
            reservation.save()

        return reservation

    def _check_available_attendees(self, exam_date, start_time, end_time):
        """
        주어진 시간대에 예약 가능한 최대 인원 수를 계산

        Args:
            exam_date: 시험 날짜
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            available_attendees: 예약 가능한 최대 인원 수
        """
        # 모든 시간대 슬롯 정보 가져오기
        all_slots = self._get_available_slots(exam_date)

        # 요청한 시간대와 겹치는 슬롯만 필터링
        slots = [
            slot for slot in all_slots
            if (start_time < slot['end_time'] and end_time > slot['start_time'])
        ]

        if not slots:
            return MAX_ATTENDEES_PER_TIMESLOT  # 겹치는 슬롯이 없으면 최대 인원 반환

        # 겹치는 슬롯 중 가장 적은 가용 인원이 실제 예약 가능 인원
        available_attendees = min(slot['available'] for slot in slots)

        return available_attendees

    def _get_available_slots(self, exam_date):
        """
        특정 날짜에 시간대와 예약 가능 인원 정보를 반환

        Args:
            exam_date: 조회할 날짜

        Returns:
            time_slots: 시간대와 가능 인원 정보 목록
            [
                {'start_time': time(9, 0), 'end_time': time(10, 0), 'available': 50000},
                {'start_time': time(10, 0), 'end_time': time(11, 0), 'available': 40000},
                ...
            ]
        """
        # 해당 날짜의 모든 확정 예약 조회
        confirmed_reservations = Reservation.objects.filter(
            status='CONFIRMED',
            exam_date=exam_date
        ).values('start_time', 'end_time', 'attendees')

        # 1시간 단위 슬롯
        time_slots = []
        current_hour = OPERATION_START_TIME.hour

        while current_hour < OPERATION_END_TIME.hour:
            slot_start = time(current_hour, 0)
            slot_end = time(current_hour + 1, 0)
            time_slots.append({
                'start_time': slot_start,
                'end_time': slot_end,
                'available': MAX_ATTENDEES_PER_TIMESLOT
            })
            current_hour += 1

        # 각 예약이 영향을 미치는 슬롯 계산
        for reservation in confirmed_reservations:
            res_start = reservation['start_time']
            res_end = reservation['end_time']
            res_attendees = reservation['attendees']

            # 예약이 영향을 미치는 모든 슬롯 업데이트
            for slot in time_slots:
                if res_start < slot['end_time'] and res_end > slot['start_time']:
                    # 해당 슬롯에 예약된 인원만큼 가용 인원 감소
                    slot['available'] -= res_attendees

        # 시간대 정보 반환
        return time_slots

    def delete_reservation(self, user, reservation):
        """
        사용자의 권한에 따라 예약을 삭제

        Args:
            reservation: 예약
            user: 요청한 사용자

        Returns:

        Raises:
            ConfirmedReservationModificationException:
                기업 사용자가 확정된 예약 삭제를 시도하는 경우
        """
        # 기업 사용자가 확정된 예약을 삭제하려는 경우 예외 처리
        if user.role == 'COMPANY' and reservation.status == 'CONFIRMED':
            raise ConfirmedReservationModificationException("확정된 예약은 삭제할 수 없습니다.")

        reservation.delete()
