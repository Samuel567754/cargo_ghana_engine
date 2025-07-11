from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from .serializers import UserSerializer, RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Public registration endpoint
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], serializer_class=RegisterSerializer)
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    # Authenticated profile endpoint
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)



    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)