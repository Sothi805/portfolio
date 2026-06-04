from django.contrib import admin
from .models import Template, Portfolio, Project, Skill, Testimonial


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0


class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 0


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'template', 'status', 'views_count', 'is_featured', 'updated_at']
    list_filter = ['status', 'is_featured', 'template']
    search_fields = ['title', 'user__username']
    inlines = [ProjectInline, SkillInline, TestimonialInline]
    actions = ['make_featured', 'make_public']

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = 'Mark selected portfolios as featured'

    def make_public(self, request, queryset):
        queryset.update(status='public')
    make_public.short_description = 'Make selected portfolios public'
