from django.db import models
from django.conf import settings


class Template(models.Model):
    """Portfolio template"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    preview_image = models.ImageField(upload_to='templates/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    """User portfolio"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('private', 'Private'),
        ('public', 'Public'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolios')
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    content = models.JSONField(default=dict)
    views_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'slug']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def get_about(self):
        return self.content.get('about', '')

    def get_contact(self):
        return self.content.get('contact', {})


class Project(models.Model):
    """Project within a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    url = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Skill(models.Model):
    """Skill listed in a portfolio"""
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='intermediate')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    """Testimonial for a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='testimonials')
    author_name = models.CharField(max_length=200)
    author_role = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.author_name} on {self.portfolio.title}"


class Education(models.Model):
    """Education entry in a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200, blank=True)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_year = models.CharField(max_length=10, blank=True)
    end_year = models.CharField(max_length=10, blank=True, help_text="Leave blank if currently studying")
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-start_year']

    def __str__(self):
        return f"{self.degree} at {self.institution}"

    @property
    def period(self):
        start = self.start_year or ''
        end = self.end_year or 'Present'
        if start:
            return f"{start} – {end}"
        return end


class Experience(models.Model):
    """Work experience entry in a portfolio"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    start_year = models.CharField(max_length=10, blank=True)
    end_year = models.CharField(max_length=10, blank=True, help_text="Leave blank if current position")
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-start_year']

    def __str__(self):
        return f"{self.role} at {self.company}"

    @property
    def period(self):
        start = self.start_year or ''
        end = self.end_year or 'Present'
        if start:
            return f"{start} – {end}"
        return end
