from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils.timezone import now
from datetime import timedelta

from apps.users.models import CustomUser
from apps.portfolios.models import Portfolio
from apps.forum.models import ForumThread, FlaggedContent, ForumReply
from apps.notifications.models import Notification
from .models import ModerationAction


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardIndexView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = CustomUser.objects.count()
        context['active_users'] = CustomUser.objects.filter(
            last_login__gte=now() - timedelta(days=30)
        ).count()
        context['total_portfolios'] = Portfolio.objects.count()
        context['public_portfolios'] = Portfolio.objects.filter(status='public').count()
        context['forum_posts'] = ForumThread.objects.count() + ForumReply.objects.count()
        context['flagged_count'] = FlaggedContent.objects.filter(status='pending').count()
        context['recent_users'] = CustomUser.objects.order_by('-date_joined')[:5]
        context['recent_portfolios'] = Portfolio.objects.select_related('user').order_by('-created_at')[:5]
        context['recent_threads'] = ForumThread.objects.select_related('user').order_by('-created_at')[:5]
        context['recent_actions'] = ModerationAction.objects.select_related('admin_user', 'target_user').order_by('-created_at')[:10]
        return context


class AdminUsersView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'admin_dashboard/users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = CustomUser.objects.all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )
        return queryset.order_by('-date_joined')

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')
        users = CustomUser.objects.filter(id__in=user_ids)

        if action == 'suspend':
            users.update(status='suspended')
            messages.success(request, f'{users.count()} users suspended.')
        elif action == 'activate':
            users.update(status='active')
            messages.success(request, f'{users.count()} users activated.')
        elif action == 'delete':
            users.update(status='deleted')
            messages.success(request, f'{users.count()} users marked as deleted.')
        return redirect('admin_users')


class AdminPortfoliosView(AdminRequiredMixin, ListView):
    model = Portfolio
    template_name = 'admin_dashboard/portfolios.html'
    context_object_name = 'portfolios'
    paginate_by = 20

    def get_queryset(self):
        queryset = Portfolio.objects.select_related('user', 'template')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        portfolio_id = request.POST.get('portfolio_id')
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)

        if action == 'feature':
            portfolio.is_featured = True
            portfolio.save()
            messages.success(request, 'Portfolio featured.')
        elif action == 'unfeature':
            portfolio.is_featured = False
            portfolio.save()
            messages.success(request, 'Portfolio unfeatured.')
        elif action == 'delete':
            portfolio.delete()
            messages.success(request, 'Portfolio deleted.')
        return redirect('admin_portfolios')


class AdminModerationView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_dashboard/moderation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reason = self.request.GET.get('reason')
        flagged = FlaggedContent.objects.filter(status='pending').select_related('reported_by')
        if reason:
            flagged = flagged.filter(reason=reason)
        context['flagged_content'] = flagged
        context['count'] = flagged.count()
        return context

    def post(self, request, *args, **kwargs):
        flag_id = request.POST.get('flag_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        flag = get_object_or_404(FlaggedContent, id=flag_id)

        target_user = None
        if action == 'delete':
            if flag.content_type == 'thread':
                thread = ForumThread.objects.filter(id=flag.content_id).first()
                if thread:
                    target_user = thread.user
                    thread.delete()
            elif flag.content_type == 'reply':
                reply = ForumReply.objects.filter(id=flag.content_id).first()
                if reply:
                    target_user = reply.user
                    reply.delete()
            flag.status = 'deleted'
        elif action == 'warn':
            flag.status = 'warned'
        elif action == 'suspend':
            if flag.content_type == 'thread':
                thread = ForumThread.objects.filter(id=flag.content_id).first()
                if thread:
                    target_user = thread.user
                    CustomUser.objects.filter(pk=thread.user.pk).update(status='suspended')
            flag.status = 'deleted'
        elif action == 'approve':
            flag.status = 'approved'

        flag.admin_notes = notes
        flag.resolved_at = now()
        flag.save()

        ModerationAction.objects.create(
            admin_user=request.user,
            action_type=action,
            target_user=target_user,
            reason=notes
        )
        messages.success(request, f'Action "{action}" applied.')
        return redirect('admin_moderation')


# ── Detail Views ───────────────────────────────────────────────────────────────

class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """Read-only profile view of any user, visible only to staff."""
    model = CustomUser
    template_name = 'admin_dashboard/user_detail.html'
    context_object_name = 'profile_user'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        context['portfolios'] = Portfolio.objects.filter(user=user).select_related('template').order_by('-created_at')
        context['threads'] = ForumThread.objects.filter(user=user).select_related('category').order_by('-created_at')[:10]
        context['replies'] = ForumReply.objects.filter(user=user).select_related('thread').order_by('-created_at')[:10]
        context['moderation_actions'] = ModerationAction.objects.filter(target_user=user).select_related('admin_user').order_by('-created_at')[:10]
        return context


class AdminPortfolioDetailView(AdminRequiredMixin, DetailView):
    """Read-only detail view of any portfolio, visible only to staff."""
    model = Portfolio
    template_name = 'admin_dashboard/portfolio_detail.html'
    context_object_name = 'portfolio'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portfolio = self.object
        context['projects'] = portfolio.projects.all()
        context['skills'] = portfolio.skills.all()
        return context


# ── Connect / Disconnect ───────────────────────────────────────────────────────

class AdminConnectView(AdminRequiredMixin, View):
    """
    Swap the admin's session to the target user (sandbox mode).
    The middleware blocks all writes while preview_mode is active.
    """

    def post(self, request, pk):
        target_user = get_object_or_404(CustomUser, pk=pk)

        if target_user == request.user:
            messages.warning(request, "You can't connect to your own account.")
            return redirect('admin_user_detail', pk=pk)

        # Save admin identity in locals BEFORE login — Django flushes the
        # session when switching users, so anything written before auth_login
        # would be lost.
        real_admin_id = request.user.pk
        real_admin_username = request.user.username

        # Switch the active session to the target user (this flushes the session)
        auth_login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')

        # Write preview flags AFTER login so they survive the session flush
        request.session['real_admin_id'] = real_admin_id
        request.session['real_admin_username'] = real_admin_username
        request.session['preview_mode'] = True

        messages.info(
            request,
            f'Preview mode: connected as {target_user.username} — '
            'all write operations are blocked and nothing will be saved.',
        )
        return redirect('portfolio_dashboard')


class AdminDisconnectView(View):
    """
    Restore the real admin session and exit sandbox mode.
    Does NOT use AdminRequiredMixin because request.user is the preview user.
    """

    def post(self, request):
        real_admin_id = request.session.get('real_admin_id')
        if not real_admin_id:
            return redirect('home')

        try:
            real_admin = CustomUser.objects.get(pk=real_admin_id, is_staff=True)
        except CustomUser.DoesNotExist:
            from django.contrib.auth import logout
            logout(request)
            return redirect('login')

        # Clear all preview flags before logging back in
        for key in ('real_admin_id', 'real_admin_username', 'preview_mode'):
            request.session.pop(key, None)

        auth_login(request, real_admin, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Preview mode ended. Welcome back.')
        return redirect('admin_dashboard')

