from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer, UserProfileUpdateSerializer
from .forms import LoginForm, RegisterForm


# ── MVT Views ──────────────────────────────────────────────────────────────────

class LoginView(View):
    template_name = 'auth/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user and user.status == 'active':
                login(request, user)
                refresh = RefreshToken.for_user(user)
                response = redirect(request.GET.get('next', 'home'))
                response.set_cookie('access_token', str(refresh.access_token), httponly=True)
                return response
            else:
                messages.error(request, 'Invalid email or password.')
        return render(request, self.template_name, {'form': form})


class RegisterView(View):
    template_name = 'auth/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            refresh = RefreshToken.for_user(user)
            response = redirect('portfolio_create')
            response.set_cookie('access_token', str(refresh.access_token), httponly=True)
            messages.success(request, f'Welcome to ProPortfolio, {user.username}!')
            return response
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        response = redirect('home')
        response.delete_cookie('access_token')
        return response


class ProfileView(LoginRequiredMixin, View):
    template_name = 'auth/profile.html'

    def get(self, request):
        return render(request, self.template_name, {'profile_user': request.user})

    def post(self, request):
        user = request.user
        username = request.POST.get('username', user.username)
        bio = request.POST.get('bio', user.bio)
        avatar = request.FILES.get('avatar')

        if username and username != user.username:
            if not CustomUser.objects.filter(username=username).exclude(pk=user.pk).exists():
                user.username = username
        user.bio = bio
        if avatar:
            user.avatar = avatar
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')


# ── DRF API Views ──────────────────────────────────────────────────────────────

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(username=email, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class MeAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
