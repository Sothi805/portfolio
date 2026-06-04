import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.text import slugify
from django.urls import reverse
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Template, Portfolio, Project, Skill, Testimonial, Education, Experience
from .serializers import PortfolioSerializer, PortfolioListSerializer
from .forms import PortfolioEditForm, ProjectForm, SkillForm, EducationForm, ExperienceForm


# ── MVT Views ──────────────────────────────────────────────────────────────────

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        from django.contrib.auth import get_user_model
        from django.db.models import Sum
        context = super().get_context_data(**kwargs)
        context['featured_portfolios'] = Portfolio.objects.filter(
            status='public', is_featured=True
        ).select_related('user', 'template')[:6]
        context['recent_portfolios'] = Portfolio.objects.filter(
            status='public'
        ).select_related('user', 'template').order_by('-created_at')[:6]
        context['templates'] = Template.objects.filter(is_active=True)[:4]

        # Platform stats
        User = get_user_model()
        context['total_portfolios'] = Portfolio.objects.filter(status='public').count()
        context['total_creators'] = User.objects.filter(is_active=True).count()
        total_views = Portfolio.objects.aggregate(v=Sum('views_count'))['v'] or 0
        context['total_views'] = total_views

        # Import here to avoid circular imports
        try:
            from apps.forum.models import ForumThread
            context['trending_threads'] = ForumThread.objects.select_related(
                'user', 'category'
            ).order_by('-views_count', '-created_at')[:5]
            context['total_threads'] = ForumThread.objects.count()
        except Exception:
            context['trending_threads'] = []
            context['total_threads'] = 0

        return context


class PortfolioListView(ListView):
    model = Portfolio
    template_name = 'portfolios/list.html'
    context_object_name = 'portfolios'
    paginate_by = 12

    def get_queryset(self):
        queryset = Portfolio.objects.filter(status='public').select_related('user', 'template').prefetch_related('skills')
        template_slug = self.request.GET.get('template')
        if template_slug:
            queryset = queryset.filter(template__slug=template_slug)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(user__username__icontains=search)
            )
        sort = self.request.GET.get('sort', '-updated_at')
        allowed_sorts = ['-updated_at', '-views_count', '-created_at', 'title']
        if sort in allowed_sorts:
            queryset = queryset.order_by(sort)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = Template.objects.filter(is_active=True)
        context['search'] = self.request.GET.get('search', '')
        context['active_template'] = self.request.GET.get('template', '')
        context['sort'] = self.request.GET.get('sort', '-updated_at')
        return context


class PortfolioDetailView(DetailView):
    model = Portfolio
    context_object_name = 'portfolio'
    slug_field = 'slug'
    slug_url_kwarg = 'portfolio_slug'

    TEMPLATE_MAP = {
        'developer-pro': 'portfolios/detail_developer.html',
        'developer': 'portfolios/detail_developer.html',
        'designer-minimal': 'portfolios/detail_minimalist.html',
        'minimalist': 'portfolios/detail_minimalist.html',
        'minimal': 'portfolios/detail_minimalist.html',
        'creative-agency': 'portfolios/detail_creative.html',
        'creative-studio': 'portfolios/detail_creative.html',
        'creative': 'portfolios/detail_creative.html',
        'research-pro': 'portfolios/detail_executive.html',
        'executive': 'portfolios/detail_executive.html',
        'professional': 'portfolios/detail_executive.html',
    }

    def get_template_names(self):
        if getattr(self, 'object', None) and self.object.template:
            slug = self.object.template.slug.lower()
            if slug in self.TEMPLATE_MAP:
                return [self.TEMPLATE_MAP[slug]]
        return ['portfolios/detail.html']

    def get_queryset(self):
        queryset = Portfolio.objects.select_related('user', 'template').prefetch_related(
            'projects', 'skills', 'testimonials', 'educations', 'experiences'
        )
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(Q(status='public') | Q(user=user))
        return queryset.filter(status='public')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        portfolio = self.object
        Portfolio.objects.filter(pk=portfolio.pk).update(views_count=portfolio.views_count + 1)
        return response


class PortfolioCreateView(LoginRequiredMixin, View):
    template_name = 'portfolios/create.html'

    def get(self, request):
        templates = Template.objects.filter(is_active=True)
        return render(request, self.template_name, {'templates': templates})

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        title = request.POST.get('title', '').strip()
        template_id = request.POST.get('template_id')
        if not title:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Portfolio title is required.'}, status=400)
            messages.error(request, 'Portfolio title is required.')
            return render(request, self.template_name, {
                'templates': Template.objects.filter(is_active=True)
            })
        slug = slugify(title)
        # Handle slug uniqueness
        base_slug = slug
        counter = 1
        while Portfolio.objects.filter(user=request.user, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        template = None
        if template_id:
            template = get_object_or_404(Template, id=template_id)

        portfolio = Portfolio.objects.create(
            user=request.user,
            template=template,
            title=title,
            slug=slug,
            content={
                'about': '',
                'projects': [],
                'skills': [],
                'contact': {
                    'email': request.user.email,
                    'phone': '',
                    'location': ''
                }
            }
        )
        if is_ajax:
            return JsonResponse({'status': 'ok', 'redirect': reverse('portfolio_edit', kwargs={'portfolio_slug': portfolio.slug})})
        messages.success(request, 'Portfolio created! Start editing it now.')
        return redirect('portfolio_edit', portfolio_slug=portfolio.slug)


class PortfolioEditView(LoginRequiredMixin, View):
    template_name = 'portfolios/edit.html'

    def get_portfolio(self, request, portfolio_slug):
        portfolio = get_object_or_404(Portfolio, slug=portfolio_slug, user=request.user)
        return portfolio

    def get(self, request, portfolio_slug):
        portfolio = self.get_portfolio(request, portfolio_slug)
        projects = portfolio.projects.all()
        skills = portfolio.skills.all()
        testimonials = portfolio.testimonials.all()
        educations = portfolio.educations.all()
        experiences = portfolio.experiences.all()
        return render(request, self.template_name, {
            'portfolio': portfolio,
            'projects': projects,
            'skills': skills,
            'testimonials': testimonials,
            'educations': educations,
            'experiences': experiences,
            'project_form': ProjectForm(),
            'skill_form': SkillForm(),
            'education_form': EducationForm(),
            'experience_form': ExperienceForm(),
            'templates': Template.objects.filter(is_active=True),
        })

    def post(self, request, portfolio_slug):
        portfolio = self.get_portfolio(request, portfolio_slug)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Auto-save JSON body requests (from initAutoSave)
        if is_ajax and 'application/json' in (request.content_type or ''):
            try:
                data = json.loads(request.body)
                section = data.get('section')
                content = data.get('content')
                if section in ['about', 'contact']:
                    portfolio.content[section] = content
                    portfolio.save(update_fields=['content'])
                    return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

        action = request.POST.get('action')
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in ['draft', 'private', 'public']:
                portfolio.status = new_status
                portfolio.save(update_fields=['status'])
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'new_status': new_status})
                messages.success(request, f'Portfolio is now {new_status}.')
        elif action == 'update_title':
            new_title = request.POST.get('title', '').strip()
            if new_title:
                portfolio.title = new_title
                portfolio.save(update_fields=['title'])
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'title': new_title})
                messages.success(request, 'Title updated.')
        elif action == 'add_project':
            form = ProjectForm(request.POST, request.FILES)
            if form.is_valid():
                project = form.save(commit=False)
                project.portfolio = portfolio
                project.save()
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'project': {
                        'id': project.id,
                        'title': project.title,
                        'description': project.description,
                        'url': project.url,
                        'image_url': project.image.url if project.image else None,
                    }})
                messages.success(request, 'Project added.')
            elif is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Project title is required.'}, status=400)
        elif action == 'add_skill':
            form = SkillForm(request.POST)
            if form.is_valid():
                skill = form.save(commit=False)
                skill.portfolio = portfolio
                skill.save()
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'skill': {
                        'id': skill.id,
                        'name': skill.name,
                        'proficiency': skill.proficiency,
                    }})
                messages.success(request, 'Skill added.')
            elif is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Please enter a skill name.'}, status=400)
        elif action == 'delete_project':
            pid = request.POST.get('project_id')
            Project.objects.filter(id=pid, portfolio=portfolio).delete()
            if is_ajax:
                return JsonResponse({'status': 'ok'})
            messages.success(request, 'Project removed.')
        elif action == 'delete_skill':
            sid = request.POST.get('skill_id')
            Skill.objects.filter(id=sid, portfolio=portfolio).delete()
            if is_ajax:
                return JsonResponse({'status': 'ok'})
            messages.success(request, 'Skill removed.')
        elif action == 'add_education':
            form = EducationForm(request.POST)
            if form.is_valid():
                edu = form.save(commit=False)
                edu.portfolio = portfolio
                edu.save()
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'education': {
                        'id': edu.id,
                        'institution': edu.institution,
                        'degree': edu.degree,
                        'field_of_study': edu.field_of_study,
                        'period': edu.period,
                        'description': edu.description,
                    }})
                messages.success(request, 'Education added.')
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'Please fill in at least the institution name.'}, status=400)
                messages.error(request, 'Please fill in at least the institution name.')
        elif action == 'delete_education':
            eid = request.POST.get('education_id')
            Education.objects.filter(id=eid, portfolio=portfolio).delete()
            if is_ajax:
                return JsonResponse({'status': 'ok'})
            messages.success(request, 'Education removed.')
        elif action == 'add_experience':
            form = ExperienceForm(request.POST)
            if form.is_valid():
                exp = form.save(commit=False)
                exp.portfolio = portfolio
                exp.save()
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'experience': {
                        'id': exp.id,
                        'company': exp.company,
                        'role': exp.role,
                        'period': exp.period,
                        'description': exp.description,
                    }})
                messages.success(request, 'Experience added.')
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'Please fill in at least the company and role.'}, status=400)
                messages.error(request, 'Please fill in at least the company and role.')
        elif action == 'delete_experience':
            xid = request.POST.get('experience_id')
            Experience.objects.filter(id=xid, portfolio=portfolio).delete()
            if is_ajax:
                return JsonResponse({'status': 'ok'})
            messages.success(request, 'Experience removed.')
        elif action == 'update_about':
            about = request.POST.get('about', '')
            portfolio.content['about'] = about
            portfolio.save(update_fields=['content'])
            if is_ajax:
                return JsonResponse({'status': 'ok'})
            messages.success(request, 'About section updated.')
        elif action == 'update_contact':
            portfolio.content['contact'] = {
                'email': request.POST.get('contact_email', ''),
                'phone': request.POST.get('contact_phone', ''),
                'location': request.POST.get('contact_location', ''),
            }
            portfolio.save(update_fields=['content'])
            if is_ajax:
                return JsonResponse({'status': 'ok'})
            messages.success(request, 'Contact info updated.')
        elif action == 'update_template':
            template_id = request.POST.get('template_id')
            if template_id:
                tpl = get_object_or_404(Template, id=template_id)
                portfolio.template = tpl
                portfolio.save(update_fields=['template'])
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'template_name': tpl.name})
                messages.success(request, f'Template changed to {tpl.name}.')

        return redirect('portfolio_edit', portfolio_slug=portfolio.slug)


class PortfolioDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'portfolios/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        portfolios = Portfolio.objects.filter(user=user).select_related('template')
        context['portfolios'] = portfolios
        context['total_views'] = sum(p.views_count for p in portfolios)
        context['total_projects'] = sum(p.projects.count() for p in portfolios)
        try:
            from apps.forum.models import UserPoints, UserBadge
            context['user_points'] = UserPoints.objects.filter(user=user).first()
            context['user_badges'] = UserBadge.objects.filter(user=user)
        except Exception:
            context['user_points'] = None
            context['user_badges'] = []
        try:
            from apps.notifications.models import Notification
            context['recent_notifications'] = Notification.objects.filter(
                user=user, read=False
            ).order_by('-created_at')[:5]
        except Exception:
            context['recent_notifications'] = []
        return context


# ── DRF API Views ──────────────────────────────────────────────────────────────

class PortfolioListAPIView(generics.ListAPIView):
    serializer_class = PortfolioListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'user__username']
    ordering_fields = ['created_at', 'views_count', 'title']

    def get_queryset(self):
        return Portfolio.objects.filter(status='public').select_related('user', 'template')


class PortfolioCreateAPIView(generics.CreateAPIView):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        title = serializer.validated_data.get('title', '')
        slug = slugify(title)
        base_slug = slug
        counter = 1
        while Portfolio.objects.filter(user=self.request.user, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        serializer.save(user=self.request.user, slug=slug)


class PortfolioDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PortfolioSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Portfolio.objects.filter(Q(status='public') | Q(user=user)).select_related('user', 'template')
        return Portfolio.objects.filter(status='public').select_related('user', 'template')
