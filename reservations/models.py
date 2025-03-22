from django.db import models

from reservations.choices import STATUS_CHOICES
from users.models import User


class Reservation(models.Model):
    company_customer = models.ForeignKey(
        User,
        verbose_name='기업 사용자',
        on_delete=models.CASCADE,
    )
    exam_date = models.DateField(
        verbose_name='시험 날짜'
    )
    start_time = models.TimeField(
        verbose_name='시작 시간'
    )
    end_time = models.TimeField(
        verbose_name='종료 시간'
    )
    attendees = models.PositiveIntegerField(
        verbose_name='응시 인원'
    )
    status = models.CharField(
        verbose_name='상태',
        choices=STATUS_CHOICES,
        max_length=50,
        default='PENDING',
    )

    class Meta:
        db_table = "reservations"

    def __str__(self):
        return f'{self.company_customer}: {self.exam_date} / {self.start_time} - {self.end_time}'
