from django.views.generic import ListView

from pombola.core.models import Organisation, OrganisationKind


class SACommitteesView(ListView):
    # .filter(
    #     contacts__kind__slug='email'
    # )
    queryset = Organisation.objects.committees()\
        .ongoing().select_related('kind').order_by('kind__id').all()
    context_object_name = 'committees'
    template_name = 'south_africa/committee_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(SACommitteesView, self).get_context_data(*args, **kwargs)
        return context
