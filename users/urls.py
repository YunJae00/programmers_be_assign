from django.urls import path

from users.views import SignInAPIView

urlpatterns = [
    path('sign-in/', SignInAPIView.as_view()),
]