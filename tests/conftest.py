import pytest
import factory
from faker import Faker
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.portfolios.models import Template, Portfolio
from apps.forum.models import ForumCategory, ForumThread

fake = Faker()
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class TemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Template

    name = factory.Faker('word')
    slug = factory.Sequence(lambda n: f'template-{n}')
    description = factory.Faker('text')
    is_active = True


class PortfolioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Portfolio

    user = factory.SubFactory(UserFactory)
    template = factory.SubFactory(TemplateFactory)
    title = factory.Faker('sentence', nb_words=4)
    slug = factory.Sequence(lambda n: f'portfolio-{n}')
    status = 'public'
    content = factory.LazyFunction(lambda: {
        'about': 'Test about text',
        'contact': {'email': 'test@example.com', 'phone': '', 'location': ''}
    })


class ForumCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ForumCategory

    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')
    description = factory.Faker('text')
    is_active = True


class ForumThreadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ForumThread

    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(ForumCategoryFactory)
    title = factory.Faker('sentence', nb_words=6)
    slug = factory.Sequence(lambda n: f'thread-{n}')
    content = factory.Faker('text')


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return AdminUserFactory()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def template(db):
    return TemplateFactory()


@pytest.fixture
def portfolio(db, user, template):
    return PortfolioFactory(user=user, template=template)


@pytest.fixture
def category(db):
    return ForumCategoryFactory()


@pytest.fixture
def thread(db, user, category):
    return ForumThreadFactory(user=user, category=category)
