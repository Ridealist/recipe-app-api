from rest_framework import generics, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.middleware import csrf
from django.conf import settings

from .serializers import UserSerializer, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""

    serializer_class = UserSerializer


class LoginView(ObtainAuthToken):
    """Create a new auth token for user"""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        response = Response()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        if user.is_active:
            response.set_cookie(
                key=settings.AUTH_TOKEN["AUTH_COOKIE"],
                value=token.key,
                secure=settings.AUTH_TOKEN["AUTH_COOKIE_SECURE"],
                httponly=settings.AUTH_TOKEN["AUTH_COOKIE_HTTP_ONLY"],
                samesite=settings.AUTH_TOKEN["AUTH_COOKIE_SAMESITE"],
            )
            csrf.get_token(request)
            response.data = {
                "Success": "Login successfully",
                "token": token.key,
            }
            return response


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""

    serializer_class = UserSerializer
    # authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return authenticated user"""
        return self.request.user
