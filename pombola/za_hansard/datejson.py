from __future__ import absolute_import
import json
from datetime import date


class DateEncoder (json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')

        return json.JSONEncoder.default(self, obj)
