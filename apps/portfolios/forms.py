from django import forms
from .models import Portfolio, Project, Skill, Testimonial, Education, Experience


INPUT_CLS = 'w-full px-sm py-xs border border-outline-variant rounded-lg focus:outline-none focus:border-primary'


class PortfolioEditForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['title', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLS}),
            'status': forms.Select(attrs={'class': INPUT_CLS}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'image', 'url']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Project title'}),
            'description': forms.Textarea(attrs={'class': INPUT_CLS, 'rows': 3, 'placeholder': 'Describe your project...'}),
            'url': forms.URLInput(attrs={'class': INPUT_CLS, 'placeholder': 'https://...'}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'proficiency']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'e.g. Python, React, Figma'}),
            'proficiency': forms.Select(attrs={'class': INPUT_CLS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proficiency'].initial = 'intermediate'


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_year', 'end_year', 'description']
        widgets = {
            'institution': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'e.g. MIT, Harvard, Stanford'}),
            'degree': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'e.g. Bachelor of Science'}),
            'field_of_study': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'e.g. Computer Science'}),
            'start_year': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': '2018'}),
            'end_year': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': '2022 (leave blank if current)'}),
            'description': forms.Textarea(attrs={'class': INPUT_CLS, 'rows': 2, 'placeholder': 'Brief description (optional)'}),
        }


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['company', 'role', 'start_year', 'end_year', 'description']
        widgets = {
            'company': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Company or organization name'}),
            'role': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': 'Job title or role'}),
            'start_year': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': '2020'}),
            'end_year': forms.TextInput(attrs={'class': INPUT_CLS, 'placeholder': '2023 (leave blank if current)'}),
            'description': forms.Textarea(attrs={'class': INPUT_CLS, 'rows': 2, 'placeholder': 'Key responsibilities and achievements'}),
        }
