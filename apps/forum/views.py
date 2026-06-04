from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count, Q, Prefetch
from django.utils.text import slugify
from django.utils.timezone import now
from django.urls import reverse
from django.views import View
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import (
    ForumCategory, ForumThread, ForumReply, UpvoteVote,
    FlaggedContent, UserBadge, UserPoints
)
from .serializers import ForumThreadSerializer, ForumReplySerializer, ForumCategorySerializer


# ── MVT Views ──────────────────────────────────────────────────────────────────

class ForumCategoryListView(ListView):
    model = ForumCategory
    template_name = 'forum/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ForumCategory.objects.filter(is_active=True).annotate(
            thread_count=Count('threads')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_threads'] = ForumThread.objects.select_related(
            'user', 'category'
        ).order_by('-created_at')[:5]
        context['top_users'] = UserPoints.objects.select_related('user').order_by('-total_points')[:5]
        return context


class ForumThreadListView(ListView):
    model = ForumThread
    template_name = 'forum/threads_list.html'
    context_object_name = 'threads'
    paginate_by = 20

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        self.category = get_object_or_404(ForumCategory, slug=category_slug, is_active=True)
        return ForumThread.objects.filter(category=self.category).select_related(
            'user'
        ).annotate(reply_count=Count('replies')).order_by('-is_pinned', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ForumThreadDetailView(View):
    template_name = 'forum/thread_detail.html'

    def get_thread(self, category_slug, thread_slug):
        return get_object_or_404(
            ForumThread,
            category__slug=category_slug,
            slug=thread_slug
        )

    def get(self, request, category_slug, thread_slug):
        thread = self.get_thread(category_slug, thread_slug)
        ForumThread.objects.filter(pk=thread.pk).update(views_count=thread.views_count + 1)
        # Only top-level replies; children are prefetched
        top_replies = (
            thread.replies
            .filter(parent__isnull=True)
            .select_related('user')
            .prefetch_related(
                Prefetch(
                    'child_replies',
                    queryset=ForumReply.objects.select_related('user').order_by('created_at'),
                )
            )
            .order_by('-is_marked_helpful', 'created_at')
        )

        user_upvoted_thread = False
        user_upvoted_replies = set()
        if request.user.is_authenticated:
            user_upvoted_thread = UpvoteVote.objects.filter(
                user=request.user, content_type='thread', content_id=thread.id
            ).exists()
            user_upvoted_replies = set(
                UpvoteVote.objects.filter(
                    user=request.user, content_type='reply'
                ).values_list('content_id', flat=True)
            )

        return render(request, self.template_name, {
            'thread': thread,
            'replies': top_replies,
            'user_upvoted_thread': user_upvoted_thread,
            'user_upvoted_replies': user_upvoted_replies,
        })

    def post(self, request, category_slug, thread_slug):
        if not request.user.is_authenticated:
            return redirect('login')

        thread = self.get_thread(category_slug, thread_slug)
        action = request.POST.get('action', 'reply')

        if action == 'reply':
            content = request.POST.get('content', '').strip()
            parent_id = request.POST.get('parent_id', '').strip()
            parent = None
            if parent_id:
                try:
                    parent = ForumReply.objects.get(pk=int(parent_id), thread=thread)
                except (ForumReply.DoesNotExist, ValueError):
                    parent = None
            if not content:
                messages.error(request, 'Reply cannot be empty.')
            else:
                ForumReply.objects.create(thread=thread, user=request.user, content=content, parent=parent)
                # Award points
                try:
                    from .tasks import award_points
                    award_points(request.user.id, 'reply_created', 2)
                except Exception:
                    pass
                # Send notification to thread author
                try:
                    from apps.notifications.models import Notification
                    if thread.user != request.user:
                        Notification.objects.create(
                            user=thread.user,
                            notification_type='reply',
                            content_id=thread.id,
                            title=f'New reply on "{thread.title[:50]}"',
                            message=f'{request.user.username} replied to your thread.'
                        )
                except Exception:
                    pass
                messages.success(request, 'Reply posted!')

        elif action == 'upvote_thread':
            vote, created = UpvoteVote.objects.get_or_create(
                user=request.user, content_type='thread', content_id=thread.id
            )
            if created:
                ForumThread.objects.filter(pk=thread.pk).update(upvotes=thread.upvotes + 1)
                messages.success(request, 'Upvoted!')
            else:
                vote.delete()
                ForumThread.objects.filter(pk=thread.pk).update(upvotes=max(0, thread.upvotes - 1))

        elif action == 'flag':
            reason = request.POST.get('reason', 'other')
            FlaggedContent.objects.get_or_create(
                content_type='thread',
                content_id=thread.id,
                reported_by=request.user,
                defaults={'reason': reason}
            )
            messages.success(request, 'Thread reported for review.')

        return redirect('forum_thread_detail', category_slug=category_slug, thread_slug=thread_slug)


class ForumCreateThreadView(LoginRequiredMixin, View):
    template_name = 'forum/create_thread.html'

    def get(self, request, category_slug):
        category = get_object_or_404(ForumCategory, slug=category_slug, is_active=True)
        return render(request, self.template_name, {'category': category})

    def post(self, request, category_slug):
        category = get_object_or_404(ForumCategory, slug=category_slug, is_active=True)
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return render(request, self.template_name, {'category': category})

        slug = slugify(title)
        base_slug = slug
        counter = 1
        while ForumThread.objects.filter(category=category, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        thread = ForumThread.objects.create(
            user=request.user,
            category=category,
            title=title,
            slug=slug,
            content=content
        )

        # Award points
        try:
            from .tasks import award_points
            award_points(request.user.id, 'thread_created', 5)
        except Exception:
            pass

        # Auto-flag check
        try:
            from .tasks import auto_flag_content
            auto_flag_content('thread', thread.id)
        except Exception:
            pass

        messages.success(request, 'Thread created!')
        return redirect('forum_thread_detail', category_slug=category.slug, thread_slug=thread.slug)


class LeaderboardView(TemplateView):
    template_name = 'forum/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top_users_points'] = UserPoints.objects.select_related('user').order_by('-total_points')[:20]
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['top_users_badges'] = User.objects.annotate(
            badge_count=Count('badges')
        ).filter(badge_count__gt=0).order_by('-badge_count')[:20]
        context['top_thread_authors'] = User.objects.annotate(
            thread_count=Count('forum_threads')
        ).filter(thread_count__gt=0).order_by('-thread_count')[:10]
        return context


class UpvoteReplyView(LoginRequiredMixin, View):
    def post(self, request, reply_id):
        reply = get_object_or_404(ForumReply, id=reply_id)
        vote, created = UpvoteVote.objects.get_or_create(
            user=request.user, content_type='reply', content_id=reply.id
        )
        if created:
            ForumReply.objects.filter(pk=reply.pk).update(upvotes=reply.upvotes + 1)
        else:
            vote.delete()
            ForumReply.objects.filter(pk=reply.pk).update(upvotes=max(0, reply.upvotes - 1))
        return redirect(
            'forum_thread_detail',
            category_slug=reply.thread.category.slug,
            thread_slug=reply.thread.slug
        )


# ── DRF API Views ──────────────────────────────────────────────────────────────

class ForumCategoryListAPIView(generics.ListAPIView):
    serializer_class = ForumCategorySerializer

    def get_queryset(self):
        return ForumCategory.objects.filter(is_active=True).annotate(
            thread_count=Count('threads')
        )


class ForumThreadListAPIView(generics.ListAPIView):
    serializer_class = ForumThreadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']

    def get_queryset(self):
        return ForumThread.objects.select_related('user', 'category').order_by('-created_at')


class ForumThreadDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ForumThreadSerializer
    queryset = ForumThread.objects.all()
    lookup_field = 'id'
