from django.db import transaction

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
