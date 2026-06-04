from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(LoginRequiredMixin, View):
    template_name = 'notifications/list.html'

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return render(request, self.template_name, {'notifications': notifications})


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        return redirect('notifications_list')


# DRF API
class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')[:50]


class MarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            Notification.objects.filter(user=request.user, pk=pk).update(read=True)
        else:
            Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'status': 'ok'})
