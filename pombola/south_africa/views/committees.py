from django.views.generic import ListView

from pombola.core.models import Organisation, OrganisationKind


class SACommitteesView(ListView):
    queryset = Organisation.objects.committees()\
        .select_related('kind').prefetch_related('contacts__kind')\
        .order_by_house_then_by('short_name').all()
    context_object_name = 'committees'
    template_name = 'south_africa/committee_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SACommitteesView, self).get_context_data(*args, **kwargs)
        return context
