from django.urls import path

from reservations.views import ReservationListView, ReservationDetailView

urlpatterns = [
    path('', ReservationListView.as_view(), name='reservations'),
    path('<int:reservation_id>/', ReservationDetailView.as_view(), name='reservation-detail')
]