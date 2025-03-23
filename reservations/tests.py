from datetime import time, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from reservations.models import Reservation
from users.models import User


class ReservationGetTestCase(APITestCase):
    def setUp(self):
        # 기업 사용자
        self.company_user_1 = User.objects.create(
            email='company_user_1@test.com',
            password='testpassword',
            name='company_user_1',
            role='COMPANY',
        )
        # 어드민
        self.admin_user_1 = User.objects.create(
            email='admin_user_1@test.com',
            password='testpassword',
            name='admin_user_1',
            role='ADMIN',
        )

        self.create_test_reservations(self.company_user_1, 15)
        self.create_test_reservations(self.admin_user_1, 10)

    def create_test_reservations(self, user, count):
        """테스트 예약 데이터 생성"""
        for i in range(count):
            Reservation.objects.create(
                company_customer=user,
                exam_date=timezone.now().date() + timedelta(days=5) + timedelta(days=i % 5),
                start_time=time(10 + i % 8, 0),
                end_time=time(12 + i % 8, 0),
                attendees=100 + i * 10,
                status="PENDING" if i % 2 == 0 else "CONFIRMED"
            )

    def test_get_reservations_by_company_user(self):
        """기업 사용자가 자신의 예약을 조회"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservations')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 15)
        self.assertEqual(response.data['results'][0].get('company_customer'), self.company_user_1.name)

        # 페이지네이션 이동 확인
        response = self.client.get(url + '?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # 두번째 페이지에 5개 표시

    def test_get_reservations_by_admin_user(self):
        """어드민 유저가 모든 예약을 조회"""
        self.client.force_authenticate(user=self.admin_user_1)

        url = reverse('reservations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 25)

        # 페이지네이션 이동 확인
        response = self.client.get(url + '?page=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # 세번째 페이지에 5개 표시

    def test_get_reservations_by_unauthorized_user(self):
        """인증되지 않은 사용자의 예약 조회 시도"""
        url = reverse('reservations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_reservations_by_wrong_role_user(self):
        """잘못된 역할을 가진 사용자의 예약 조회 시도"""
        self.basic_user_1 = User.objects.create(
            email='basic_user_1@test.com',
            password='testpassword',
            name='basic_user_1',
            role='BASIC', # 잘못된 역할
        )

        self.client.force_authenticate(user=self.basic_user_1)

        url = reverse('reservations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], '엑세스 권한이 없습니다.')


class ReservationCreateTestCase(APITestCase):
    def setUp(self):
        # 기업 사용자
        self.company_user_1 = User.objects.create(
            email='company_user_1@test.com',
            password='testpassword',
            name='company_user_1',
            role='COMPANY',
        )
        # 어드민
        self.admin_user_1 = User.objects.create(
            email='admin_user_1@test.com',
            password='testpassword',
            name='admin_user_1',
            role='ADMIN',
        )

    def test_create_reservation_by_company_user(self):
        """기업 사용자가 예약 생성"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'attendees': 10000,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_customer'], self.company_user_1.name)
        self.assertEqual(response.data['exam_date'], valid_data['exam_date'].isoformat())
        self.assertEqual(response.data['start_time'], valid_data['start_time'].isoformat())
        self.assertEqual(response.data['end_time'], valid_data['end_time'].isoformat())
        self.assertEqual(response.data['attendees'], valid_data['attendees'])
        self.assertEqual(response.data['status'], 'PENDING')

    def test_create_reservation_by_unauthorized_user(self):
        """인증되지 않은 사용자의 예약 생성 시도"""
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'attendees': 10000,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reservation_by_wrong_role_user(self):
        """기업 사용자가 아닌 사용자가 예약 생성 시도"""
        self.client.force_authenticate(user=self.admin_user_1)
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'attendees': 10000,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], '엑세스 권한이 없습니다.')

    def test_post_reservation_with_invalid_exam_date(self):
        """3일 이내의 날짜에 예약을 시도"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=3),
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'attendees': 10000,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '예약은 시험 시작 3일 전까지 신청 가능합니다.')

    def test_post_reservation_with_invalid_exam_time(self):
        """종료 시간이 시작 시간보다 앞선 경우 시도"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(10, 0),
            'end_time': time(10, 0),
            'attendees': 10000,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '종료 시간은 시작 시간보다 늦어야합니다.')

    def test_post_reservation_with_invalid_attendees(self):
        """신청 인원이 5만명을 넘은 경우 시도"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(10, 0),
            'end_time': time(12, 0),
            'attendees': 50001,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '응시 인원은 1명에서 50000명 사이여야 합니다.')

    def test_post_reservation_with_already_confirmed_attendees(self):
        """예약 시도 시간에 이미 일정 응시 인원이 있어 예약 불가능한 경우 시도"""
        Reservation.objects.create(
            company_customer=self.admin_user_1,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(12, 0),
            attendees=30000,
            status="CONFIRMED"
        )

        Reservation.objects.create(
            company_customer=self.admin_user_1,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(13, 0),
            end_time=time(15, 0),
            attendees=30000,
            status="CONFIRMED"
        )

        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservations')

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(11, 0),
            'end_time': time(14, 0),
            'attendees': 30000,
        }

        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '동 시간대 최대 50000명 까지 예약할 수 있습니다. (현재 예약 가능 인원: 20000명)')


class ReservationDetailGetTestCase(APITestCase):
    def setUp(self):
        # 기업 사용자 1
        self.company_user_1 = User.objects.create(
            email='company_user_1@test.com',
            password='testpassword',
            name='company_user_1',
            role='COMPANY',
        )
        # 기업 사용자 2
        self.company_user_2 = User.objects.create(
            email='company_user_2@test.com',
            password='testpassword',
            name='company_user_2',
            role='COMPANY',
        )
        # 어드민
        self.admin_user_1 = User.objects.create(
            email='admin_user_1@test.com',
            password='testpassword',
            name='admin_user_1',
            role='ADMIN',
        )

        # 기업 사용자 1의 예약
        self.reservation_1 = Reservation.objects.create(
            company_customer=self.company_user_1,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(12, 0),
            attendees=30000,
        )
        # 기업 사용자 2의 예약
        self.reservation_2 = Reservation.objects.create(
            company_customer=self.company_user_2,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(13, 0),
            end_time=time(15, 0),
            attendees=30000,
        )

    def test_get_reservation_by_id(self):
        """기업 사용자가 자신의 예약을 조회"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_customer'], self.company_user_1.name)
        self.assertEqual(response.data['exam_date'], self.reservation_1.exam_date.isoformat())
        self.assertEqual(response.data['start_time'], self.reservation_1.start_time.isoformat())
        self.assertEqual(response.data['end_time'], self.reservation_1.end_time.isoformat())
        self.assertEqual(response.data['attendees'], self.reservation_1.attendees)
        self.assertEqual(response.data['status'], 'PENDING')

    def test_get_reservation_by_unauthorized_user(self):
        """인증되지 않은 사용자의 예약 조회 시도"""
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_reservation_by_other_user(self):
        """기업 사용자 1의 예약을 기업 사용자 2가 조회 시도"""
        self.client.force_authenticate(user=self.company_user_2)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], '해당 예약에 접근할 권한이 없습니다.')

    def test_get_reservation_not_found(self):
        """없는 예약 조회 시도"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[9999])

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], '해당 예약을 찾을 수 없습니다.')


class ReservationPatchTestCase(APITestCase):
    def setUp(self):
        # 기업 사용자 1
        self.company_user_1 = User.objects.create(
            email='company_user_1@test.com',
            password='testpassword',
            name='company_user_1',
            role='COMPANY',
        )
        # 기업 사용자 2
        self.company_user_2 = User.objects.create(
            email='company_user_2@test.com',
            password='testpassword',
            name='company_user_2',
            role='COMPANY',
        )
        # 어드민
        self.admin_user_1 = User.objects.create(
            email='admin_user_1@test.com',
            password='testpassword',
            name='admin_user_1',
            role='ADMIN',
        )

        # 기업 사용자 1의 예약
        self.reservation_1 = Reservation.objects.create(
            company_customer=self.company_user_1,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(12, 0),
            attendees=30000,
        )
        # 기업 사용자 2의 예약
        self.reservation_2 = Reservation.objects.create(
            company_customer=self.company_user_2,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(13, 0),
            end_time=time(15, 0),
            attendees=30000,
        )

    def test_patch_reservation_by_company_user(self):
        """기업 사용자가 자신의 예약을 수정"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(11, 0),
            'end_time': time(14, 0),
            'attendees': 30000,
        }

        response = self.client.patch(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_customer'], self.company_user_1.name)
        self.assertEqual(response.data['start_time'], valid_data.get('start_time').isoformat())
        self.assertEqual(response.data['end_time'], valid_data.get('end_time').isoformat())
        self.assertEqual(response.data['attendees'], valid_data.get('attendees'))
        self.assertEqual(response.data['status'], 'PENDING')

    def test_patch_reservation_by_admin_user(self):
        """어드민이 기업 사용자의 예약을 수정"""
        self.client.force_authenticate(user=self.admin_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(16, 0),
            'end_time': time(18, 0),
            'attendees': 20000,
        }

        response = self.client.patch(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_customer'], self.company_user_1.name)
        self.assertEqual(response.data['start_time'], valid_data.get('start_time').isoformat())
        self.assertEqual(response.data['end_time'], valid_data.get('end_time').isoformat())
        self.assertEqual(response.data['attendees'], valid_data.get('attendees'))
        self.assertEqual(response.data['status'], 'PENDING')

    def test_patch_reservation_by_other_user(self):
        """기업 사용자 1의 예약을 기업 사용자 2가 수정을 시도"""
        self.client.force_authenticate(user=self.company_user_2)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(16, 0),
            'end_time': time(18, 0),
            'attendees': 20000,
        }

        response = self.client.patch(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], '해당 예약에 접근할 권한이 없습니다.')

    def test_patch_reservation_by_unauthorized_user(self):
        """인증되지 않은 사용자의 예약 수정 시도"""
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(16, 0),
            'end_time': time(18, 0),
            'attendees': 20000,
        }

        response = self.client.patch(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_reservation_not_found(self):
        """"기업 사용자가 존재하지 않는 예약을 수정 시도"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[9999])

        valid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(16, 0),
            'end_time': time(18, 0),
            'attendees': 20000,
        }

        response = self.client.patch(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], '해당 예약을 찾을 수 없습니다.')

    def test_patch_reservation_status_by_non_admin(self):
        """어드민 사용자가 아닌 다른 사용자가 status를 수정 시도할 경우"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        valid_data = {
            'status': 'CONFIRMED'
        }

        response = self.client.patch(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], '상태 수정은 어드민 사용자만 가능합니다.')

    def test_patch_reservation_with_invalid_exam_date(self):
        """예약일이 시험 시작 3일 이내인 경우"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        invalid_data = {
            'exam_date': timezone.now().date() + timedelta(days=3),
        }

        response = self.client.patch(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '예약은 시험 시작 3일 전까지 신청 가능합니다.')

    def test_patch_reservation_with_invalid_time(self):
        """종료 시간이 시작 시간보다 앞서거나 같은 경우"""
        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        invalid_data = {
            'start_time': time(12, 0),
            'end_time': time(9, 0),
        }

        response = self.client.patch(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '종료 시간은 시작 시간보다 늦어야합니다.')

    def test_patch_reservation_with_invalid_attendees(self):
        """해당 시간 응시 인원이 5만명을 넘어갈 경우"""
        Reservation.objects.create(
            company_customer=self.company_user_1,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(10, 0),
            end_time=time(12, 0),
            attendees=30000,
            status='CONFIRMED'
        )

        Reservation.objects.create(
            company_customer=self.company_user_1,
            exam_date=timezone.now().date() + timedelta(days=5),
            start_time=time(15, 0),
            end_time=time(16, 0),
            attendees=10000,
            status='CONFIRMED'
        )

        self.client.force_authenticate(user=self.company_user_1)
        url = reverse('reservation-detail', args=[self.reservation_1.id])

        invalid_data = {
            'exam_date': timezone.now().date() + timedelta(days=5),
            'start_time': time(11, 0),
            'end_time': time(16, 0),
            'attendees': 20001,
        }

        response = self.client.patch(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], '동 시간대 최대 50000명 까지 예약할 수 있습니다. (현재 예약 가능 인원: 20000명)')
