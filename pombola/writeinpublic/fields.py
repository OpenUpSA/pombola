from functools import partial
from itertools import groupby
from operator import attrgetter

from django.forms.models import ModelChoiceIterator, ModelChoiceField, ChoiceField


class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, field, groupby):
        if isinstance(groupby, str):
            groupby = attrgetter(groupby)
        elif not callable(groupby):
            raise TypeError(
                "choices_groupby must either be a str or a callable accepting a single argument"
            )
        self.groupby = groupby
        super(GroupedModelChoiceIterator, self).__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.groupby):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelChoiceField(ModelChoiceField):
    """
    A ModelChoiceField that is grouped by some value using the choices_groupby
    argument.

    Copied and modified from https://code.djangoproject.com/ticket/27331
    """

    def __init__(self, choices_groupby, queryset, *args, **kwargs):
        self.choices_groupby = choices_groupby
        super(GroupedModelChoiceField, self).__init__(queryset, *args, **kwargs)

    def _get_choices(self):
        return GroupedModelChoiceIterator(self, groupby=self.choices_groupby)

    choices = property(_get_choices, ChoiceField._set_choices)
