from django.db import DatabaseError
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from programmers_exam_reservation.utils.paginations import CustomPagination
from programmers_exam_reservation.utils.permissions import HasRolePermission
from reservations.managers import ReservationManager
from reservations.serializers import ReservationResponseSerializer, ReservationRequestSerializer


class ReservationListView(GenericAPIView):
    serializer_class = ReservationResponseSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), HasRolePermission(['COMPANY', 'ADMIN'])]
        if self.request.method == 'POST':
            return [IsAuthenticated(), HasRolePermission(['COMPANY'])]
        return [IsAuthenticated()]

    def get(self, request):
        """
        예약 조회
        - 어드민: 모든 예약 조회 가능
        - 기업 사용자: 자신의 예약 조회 가능
        """
        manager = ReservationManager()

        try:
            reservations_qs = manager.retrieve_reservations_by_user(request.user)
            # 페이지네이션 적용
            paginated_reservations_qs = self.paginate_queryset(reservations_qs)

            response_serializer = self.serializer_class(paginated_reservations_qs, many=True)

            return Response(
                data=self.paginator.get_paginated_data(response_serializer.data),
                status=status.HTTP_200_OK
            )
        except DatabaseError as e:
            return Response(
                {"detail": "데이터베이스 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        예약 생성
        - 기업 사용자: 예약 생성
        """
        manager = ReservationManager()

        try:
            request_serializer = ReservationRequestSerializer(data=request.data)
            request_serializer.is_valid(raise_exception=True)

            created_reservation = manager.create_reservation(
                request.user,
                request_serializer.validated_data.get('exam_date'),
                request_serializer.validated_data.get('start_time'),
                request_serializer.validated_data.get('end_time'),
                request_serializer.validated_data.get('attendees'),
            )

            response_serializer = self.serializer_class(created_reservation)

            return Response(
                data=response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except DatabaseError as e:
            return Response(
                {"detail": "데이터베이스 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReservationDetailView(GenericAPIView):
    serializer_class = ReservationResponseSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), HasRolePermission(['COMPANY', 'ADMIN'])]
        return [IsAuthenticated()]

    def get(self, request, reservation_id):
        """
        예약 정보 조회
        - 어드민 유저: 모든 예약 접근 가능
        - 기업 유저: 자신의 예약만 접근 가능
        """
        manager = ReservationManager()

        try:
            reservation_qs = manager.retrieve_reservation_by_id(request.user, reservation_id)

            response_serializer = self.serializer_class(reservation_qs)

            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
            )
        except DatabaseError as e:
            return Response(
                {"detail": "데이터베이스 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
