# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
import random


register = template.Library()

@register.filter()
def getallattrs(value):
    return dir(value)

@register.filter()
def rand():
    return random.randrange(1, 4)