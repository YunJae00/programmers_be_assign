from django.db import DatabaseError
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from programmers_exam_reservation.utils.paginations import CustomPagination
from programmers_exam_reservation.utils.permissions import HasRolePermission
from reservations.managers import ReservationManager
from reservations.serializers import ReservationResponseSerializer, ReservationRequestSerializer, \
    ReservationAvailableTimeResponseSerializer


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
        if self.request.method == 'PATCH':
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

    def patch(self, request, reservation_id):
        """
        예약 내용 수정
        - 어드민: 예약을 확정, 예약 내용 수정
        - 기업 사용자: 예약 내용 수정
        """
        manager = ReservationManager()

        request_serializer = ReservationRequestSerializer(data=request.data, partial=True)
        request_serializer.is_valid(raise_exception=True)

        try:
            reservation_qs = manager.retrieve_reservation_by_id(request.user, reservation_id)

            updated_reservation = manager.update_reservation(
                reservation_qs,
                request.user,
                request_serializer.validated_data.get('exam_date'),
                request_serializer.validated_data.get('start_time'),
                request_serializer.validated_data.get('end_time'),
                request_serializer.validated_data.get('attendees'),
                request_serializer.validated_data.get('status')
            )

            response_serializer = self.serializer_class(updated_reservation)

            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
            )
        except DatabaseError as e:
            return Response(
                {"detail": "데이터베이스 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, reservation_id):
        """
        예약 삭제
        - 어드민: 모든 예약 삭제 가능
        - 기업 사용자: 확정 전의 자신의 예약 삭제 가능
        """
        manager = ReservationManager()

        try:
            reservation_qs = manager.retrieve_reservation_by_id(request.user, reservation_id)

            manager.delete_reservation(request.user, reservation_qs)

            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        except DatabaseError as e:
            return Response(
                {"detail": "데이터베이스 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AvailableTimeView(GenericAPIView):
    serializer_class = ReservationAvailableTimeResponseSerializer

    def get_permissions(self):
        return [IsAuthenticated(), HasRolePermission(['COMPANY', 'ADMIN'])]

    def get(self, request):
        """
        - 어드민, 기업 사용자: 예약 가능한 시간대 조회
        """
        manager = ReservationManager()

        try:
            date = request.query_params.get('date')
            available_times = manager.retrieve_available_times(date)

            response_serializer = self.serializer_class(available_times, many=True)

            return Response(
                data=response_serializer.data,
                status=status.HTTP_200_OK
            )
        except DatabaseError as e:
            return Response(
                {"detail": "데이터베이스 처리 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
