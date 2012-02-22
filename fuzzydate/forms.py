# $Id: forms.py 620 2010-08-05 10:55:36Z gnoel $

import re, time, datetime
from django.forms import widgets
from django.forms import fields
from core import FuzzyDate
from django.forms.util import ErrorList, ValidationError

__all__ = (
    'FuzzyDateInput',
    'FuzzyDateField'
)

class FuzzyDateInput(widgets.DateTimeInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, FuzzyDate):
            value = value.getDateFrom().__str__()
        return super(FuzzyDateInput, self).render(name, value, attrs)

class FuzzyDateField(fields.DateField):
    widget = FuzzyDateInput

    def clean(self, value):
        #raise Exception, "Where am I?" 
        if isinstance(value, FuzzyDate):
            return value
        ret = FuzzyDate()
        if (not ret.setAsString(value)):
            #raise ValidationError(u'Invalid date format "%s". Specify a single date ("yyyy-mm-dd", "yyyy-mm" or "yyyy") or a date range, e.g. "2004 to 2009"')
            raise ValidationError('''Invalid date format. Examples: '24-12-1970', '12-1970', '1970', '1970 to 1975', 'c. 1970', '?1970' (%s)''' % ret.getLastError())
        else:
            # don't return it or populate fuzzydate with the return value
            # as it has already been set properly
            # we only want to raise an error if the value is invalid as a date field
            # todo: support for None values
            super(FuzzyDateField, self).clean(ret.getDateFrom())
        return ret

