from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, LoginHistorySerializer
from .models import LoginHistory

# Create your views here.
User = get_user_model()

class LoginHistoryPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            user = User.objects.get(username=request.data.get('username'))
            LoginHistory.objects.create(user=user)
            
        return response


class UserLoginHistoryView(generics.ListAPIView):
    serializer_class = LoginHistorySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LoginHistoryPagination

    def get_queryset(self):
        return LoginHistory.objects.filter(user=self.request.user)