import pytest
from apps.portfolios.models import Portfolio, Project, Skill
from tests.conftest import UserFactory, TemplateFactory, PortfolioFactory


@pytest.mark.django_db
class TestPortfolioModel:

    def test_create_portfolio(self):
        user = UserFactory()
        template = TemplateFactory()
        portfolio = Portfolio.objects.create(
            user=user, template=template,
            title='My Portfolio', slug='my-portfolio', status='public'
        )
        assert portfolio.user == user
        assert portfolio.title == 'My Portfolio'
        assert portfolio.status == 'public'
        assert portfolio.views_count == 0

    def test_portfolio_slug_unique_per_user(self):
        user = UserFactory()
        template = TemplateFactory()
        Portfolio.objects.create(user=user, template=template, title='P1', slug='same-slug', status='public')
        with pytest.raises(Exception):
            Portfolio.objects.create(user=user, template=template, title='P2', slug='same-slug', status='public')

    def test_portfolio_statuses(self):
        user = UserFactory()
        for i, status in enumerate(['draft', 'private', 'public']):
            p = Portfolio.objects.create(user=user, title=f'P{i}', slug=f'p-{i}', status=status)
            assert p.status == status

    def test_default_status_is_draft(self):
        user = UserFactory()
        p = Portfolio.objects.create(user=user, title='Draft P', slug='draft-p')
        assert p.status == 'draft'


@pytest.mark.django_db
class TestProjectModel:

    def test_add_project(self, portfolio):
        project = Project.objects.create(
            portfolio=portfolio, title='Project 1', description='Great project'
        )
        assert project.portfolio == portfolio
        assert portfolio.projects.count() == 1

    def test_project_ordering(self, portfolio):
        Project.objects.create(portfolio=portfolio, title='Third', description='', order=3)
        Project.objects.create(portfolio=portfolio, title='First', description='', order=1)
        Project.objects.create(portfolio=portfolio, title='Second', description='', order=2)
        titles = list(portfolio.projects.values_list('title', flat=True))
        assert titles == ['First', 'Second', 'Third']


@pytest.mark.django_db
class TestSkillModel:

    def test_add_skill(self, portfolio):
        skill = Skill.objects.create(portfolio=portfolio, name='Python', proficiency='expert')
        assert skill.portfolio == portfolio
        assert skill.name == 'Python'
