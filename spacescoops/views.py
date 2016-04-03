from django.http import Http404
# from django.http import HttpResponse
# from django.template import RequestContext, loader

# from django.shortcuts import get_object_or_404, render

from django.views.generic import ListView, DetailView
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from parler.views import TranslatableSlugMixin, ViewUrlMixin, FallbackLanguageResolved
from django.utils.translation import ugettext as _

from .models import Article, Category
from institutions.models import Institution

# def index(request):
#     objs = Article.objects.all()
#     context = {
#         'objects': objs,
#     }
#     return render(request, 'articles/index.html', context)

# def detail(request, object_id):
#     obj = get_object_or_404(Article, pk=object_id)
#     return render(request, 'articles/detail.html', {'object': obj})


def _article_queryset(request, only_translations=True):
    qs = Article.objects.available(user=request.user)
    if only_translations:
        qs = qs.active_translations()
    # qs = qs.prefetch_related('translations')
    # qs = qs.prefetch_related('categories')
    # qs = qs.prefetch_related('images__file')
    qs = Article.add_prefetch_related(qs)
    return qs


class ArticleListView(ViewUrlMixin, ListView):
    # template_name = 'articles/article_list.html'
    page_template_name = 'spacescoops/article_list_page.html'
    # context_object_name = 'object_list'
    # model = Article
    view_url_name = 'scoops:list'
    # paginate_by = 10

    def get_queryset(self):
        qs = _article_queryset(self.request)
        if 'category' in self.kwargs:
            category = self.kwargs['category']
            qs = qs.filter(**{category: True})
        return qs

    def get_view_url(self):
        if 'category' in self.kwargs:
            return reverse('scoops:list_by_category', kwargs={'category': self.kwargs['category']})
        else:
            return super().get_view_url()

    def get_template_names(self):
        if self.request.is_ajax():
            return [self.page_template_name]
        else:
            return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_template'] = self.page_template_name
        return context


class ArticleDetailView(DetailView):
    # model = Article
    # template_name = 'articles/article_detail.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_queryset(self, only_translations=False):
        qs = _article_queryset(self.request, only_translations=only_translations)
        qs = qs.prefetch_related('originalnews_set')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['random'] = self.get_queryset(only_translations=True).order_by('?')[:3]
        return context


def detail_by_code(request, code):
    'When only the code is provided, redirect to the canonical URL'
    try:
        obj = _article_queryset(request).get(code=code)
    except Article.DoesNotExist:
        raise Http404(_('Article does not exist'))
    return redirect(obj, permanent=True)


def _category_queryset(request):
    qs = Category.objects.all()
    # qs = qs.active_translations()  # this will disable categories for "untranslated" languages
    qs = qs.prefetch_related('articles__categories__translations')
    qs = qs.prefetch_related('translations')
    # return Category.add_prefetch_related(qs)
    return qs


class CategoryListView(ViewUrlMixin, ListView):
    # template_name = 'categories/category_list.html'
    # context_object_name = 'object_list'
    # model = Category
    view_url_name = 'categories:list'

    def get_queryset(self):
        qs = _category_queryset(self.request)
        return qs


class CategoryDetailView(TranslatableSlugMixin, DetailView):
    # model = Category
    # template_name = 'categories/category_detail.html'

    def get_language_choices(self):
        return [self.get_language(), 'en']  # TODO: nasty hack!

    def get_queryset(self):
        qs = _category_queryset(self.request)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = context['object'].articles.active_translations()
        return context


def _partner_queryset(request):
    qs = Institution.objects.all()
    qs = Article.add_prefetch_related(qs, 'scoops')
    return qs


class PartnerListView(ListView):
    template_name = 'spacescoops/partner_list.html'
    view_url_name = 'partners:list'

    def get_queryset(self):
        qs = _partner_queryset(self.request).order_by('-spacescoop_count')
        return qs


class PartnerDetailView(DetailView):
    template_name = 'spacescoops/partner_detail.html'

    def get_queryset(self):
        qs = _partner_queryset(self.request)
        return qs