from info.views import InfoBlogView, InfoPageView

from django.views.generic import DetailView, ListView
from django.views.generic.base import ContextMixin

from info.models import InfoPage, Category, Tag, ViewCount

from django.conf import settings
from datetime import date, timedelta
from django.db.models import F, Sum


class LazyTagLookup(object):
    def __getitem__(self, tag_slug):
        return InfoPage.objects.filter(tags__slug=tag_slug)

class BlogMixin(ContextMixin):

    def get_context_data(self, **kwargs):
        context = super(BlogMixin, self).get_context_data(**kwargs)

        context['all_categories'] = Category.objects.all().order_by('name')

        context['all_posts'] = InfoPage.objects.filter(kind=InfoPage.KIND_BLOG).order_by("-publication_date")
        
        context['posts_in_cat_week_parliament'] = InfoPage.objects.filter(categories__slug__contains='week-parliament').order_by("-publication_date")[:6]
        context['posts_in_cat_mp_corner'] = InfoPage.objects.filter(categories__slug__contains='mp-corner').order_by("-publication_date")[:6]
        context['posts_in_cat_interviews_research'] = InfoPage.objects.filter(categories__slug__contains='interviews-research').order_by("-publication_date")[:6]
        context['posts_in_cat_legislation'] = InfoPage.objects.filter(categories__slug__contains='legislation').order_by("-publication_date")[:6]
        context['posts_in_cat_understanding_government'] = InfoPage.objects.filter(categories__slug__contains='understanding-government').order_by("-publication_date")[:6]
        
        context['posts_in_cat_featured'] = InfoPage.objects.filter(categories__slug__contains='featured').order_by("-publication_date")

        context['recent_posts'] = InfoPage.objects \
            .filter(kind=InfoPage.KIND_BLOG) \
            .order_by("-publication_date")


        context['some_popular_posts'] = viewcounts = ViewCount.objects.filter(
            page__kind=InfoPage.KIND_BLOG
        ).count()


        if viewcounts:
            # We randomize the order of blog posts with the same number
            # of views - this is only really useful when we have
            # very little data, since with more data it's unlikely
            # there will be many pages with the same number of view
            # counts in the recent period anyway
            randomize_same_sum = viewcounts < 20
            context['popular_posts'] = self.popular_posts_queryset(
                only_recent_posts=False,
                randomize_same_sum=randomize_same_sum)
            context['popular_recent_posts'] = self.popular_posts_queryset(
                only_recent_posts=True,
                randomize_same_sum=randomize_same_sum)

        context['posts_by_tag'] = LazyTagLookup()


        return context

    def popular_posts_queryset(self, only_recent_posts, randomize_same_sum):
        date_condition = {}
        if only_recent_posts:
            date_condition = {
                'publication_date__gte': date.today() - timedelta(days=28)}

        # The '?' means to randomize the order among counts that
        # are the same
        if randomize_same_sum:
            order_args = ('-viewcount__count__sum', '?')
        else:
            order_args = ('-viewcount__count__sum',)

        return (
            InfoPage.objects
            .filter(kind=InfoPage.KIND_BLOG)
            .filter(**date_condition)
            .filter(viewcount__count__gt=0)
            .filter(viewcount__date__gte=date.today() - timedelta(days=28))
            .annotate(Sum('viewcount__count'))
            .order_by(*order_args))


    

class SANewsletterPage(InfoPageView):
    template_name = 'south_africa/info_newsletter.html'


class SAInfoBlogList(BlogMixin,ListView):
    """Show list of blog posts"""
    model = InfoPage
    queryset = InfoPage.objects.filter(kind=InfoPage.KIND_BLOG).order_by("-publication_date")
    paginate_by = settings.INFO_POSTS_PER_LIST_PAGE
    template_name = 'info/blog_list.html'

class SAInfoBlogView(BlogMixin, InfoBlogView):
    pass
