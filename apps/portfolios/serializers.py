from rest_framework import serializers
from .models import Template, Portfolio, Project, Skill, Testimonial
from apps.users.serializers import UserSerializer


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'slug', 'description', 'preview_image']


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'image', 'url', 'order']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'proficiency', 'order']


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'author_name', 'author_role', 'content', 'rating', 'order']


class PortfolioSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    testimonials = TestimonialSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    template = TemplateSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=Template.objects.all(), source='template', write_only=True, required=False
    )

    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'template', 'template_id', 'title', 'slug',
            'status', 'content', 'views_count', 'is_featured',
            'projects', 'skills', 'testimonials',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'views_count', 'slug', 'created_at', 'updated_at']


class PortfolioListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    template = TemplateSerializer(read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'user', 'template', 'title', 'slug', 'status', 'views_count', 'is_featured', 'updated_at']
