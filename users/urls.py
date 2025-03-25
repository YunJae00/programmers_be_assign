from django.urls import path

from users.views import SignInAPIView, SignUpAPIView

urlpatterns = [
    path("sign-up/", SignUpAPIView.as_view()),
    path('sign-in/', SignInAPIView.as_view()),
]