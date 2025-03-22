from django.urls import path

from reservations.views import ReservationListView

urlpatterns = [
    path('', ReservationListView.as_view(), name='reservations')
]