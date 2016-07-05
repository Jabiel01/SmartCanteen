from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
import re
from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import Widget, Select, MultiWidget
from django.utils.safestring import mark_safe

from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.forms.widgets import Select, MultiWidget, DateInput, TextInput, Widget
from django.forms.extras.widgets import SelectDateWidget
from time import strftime
import re
from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import Widget, Select, MultiWidget
from django.utils.safestring import mark_safe


import re
from django.utils.safestring import mark_safe
# from setuptools.compat import basestring
# from setuptools.compat import basestring


class MultiSelectWidget(forms.SelectMultiple):
    class Media:
        css = {
            'all': (
                settings.MEDIA_URL + 'js/michael-multiselect/css/ui.multiselect.css',
            )
        }
        js = (
            settings.MEDIA_URL + 'js/michael-multiselect/js/plugins/tmpl/jquery.tmpl.1.1.1.js',
            settings.MEDIA_URL + 'js/michael-multiselect/js/plugins/blockUI/jquery.blockUI.js',
            settings.MEDIA_URL + 'js/michael-multiselect/js/ui.multiselect.js',
        )

    def __init__(self, language=None, attrs=None):
        self.language = language or settings.LANGUAGE_CODE[:2]
        super(MultiSelectWidget, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None):
        rendered = super(MultiSelectWidget, self).render(name, value, attrs)
        return rendered + mark_safe(u'''<script type="text/javascript">
            $(document).ready(function afterReady() {
                var elem = $('#id_%(name)s');
                elem.multiselect();
            });
            </script>''' % {'name': name})


"""
Widget for datetime split, with calendar for date, and drop-downs for times.
"""


__all__ = ('SelectTimeWidget', 'SplitSelectDateTimeWidget')

# Attempt to match many time formats:
# Example: "12:34:56 P.M."  matches:
# ('12', '34', ':56', '56', 'P.M.', 'P', '.', 'M', '.')
# ('12', '34', ':56', '56', 'P.M.')
# Note that the colon ":" before seconds is optional, but only if seconds are omitted
time_pattern = r'(\d\d?):(\d\d)(:(\d\d))? *([aApP]\.?[mM]\.?)?$'

RE_TIME = re.compile(time_pattern)
# The following are just more readable ways to access re.matched groups:
HOURS = 0
MINUTES = 1
SECONDS = 3
MERIDIEM = 4


class SelectTimeWidget(Widget):
    """
    A Widget that splits time input into <select> elements.
    Allows form to show as 24hr: <hour>:<minute>:<second>, (default)
    or as 12hr: <hour>:<minute>:<second> <am|pm>

    Also allows user-defined increments for minutes/seconds
    """
    hour_field = '%s_hour'
    minute_field = '%s_minute'
    meridiem_field = '%s_meridiem'
    twelve_hr = False  # Default to 24hr.

    def __init__(self, attrs=None, hour_step=None, minute_step=None, twelve_hr=False):
        """
        hour_step, minute_step, second_step are optional step values for
        for the range of values for the associated select element
        twelve_hr: If True, forces the output to be in 12-hr format (rather than 24-hr)
        """
        self.attrs = attrs or {}

        if twelve_hr:
            self.twelve_hr = True  # Do 12hr (rather than 24hr)
            self.meridiem_val = 'a.m.'  # Default to Morning (A.M.)

        if hour_step and twelve_hr:
            self.hours = range(1, 13, hour_step)
        elif hour_step:  # 24hr, with stepping.
            self.hours = range(0, 24, hour_step)
        elif twelve_hr:  # 12hr, no stepping
            self.hours = range(1, 13)
        else:  # 24hr, no stepping
            self.hours = range(0, 24)

        if minute_step:
            self.minutes = range(0, 60, minute_step)
        else:
            self.minutes = range(0, 60)

    def render(self, name, value, attrs=None):
        try:  # try to get time values from a datetime.time object (value)
            hour_val, minute_val = value.hour, value.minute
            if self.twelve_hr:
                if hour_val >= 12:
                    self.meridiem_val = 'p.m.'
                else:
                    self.meridiem_val = 'a.m.'
        except AttributeError:
            hour_val = minute_val = 0
            if isinstance(value, basestring):
                match = RE_TIME.match(value)
                if match:
                    time_groups = match.groups();
                    hour_val = int(time_groups[HOURS]) % 24  # force to range(0-24)
                    minute_val = int(time_groups[MINUTES])

                    # check to see if meridiem was passed in
                    if time_groups[MERIDIEM] is not None:
                        self.meridiem_val = time_groups[MERIDIEM]
                    else:  # otherwise, set the meridiem based on the time
                        if self.twelve_hr:
                            if hour_val >= 12:
                                self.meridiem_val = 'p.m.'
                            else:
                                self.meridiem_val = 'a.m.'
                        else:
                            self.meridiem_val = None

        # If we're doing a 12-hr clock, there will be a meridiem value, so make sure the
        # hours get printed correctly
        if self.twelve_hr and self.meridiem_val:
            if self.meridiem_val.lower().startswith('p') and hour_val > 12 and hour_val < 24:
                hour_val = hour_val % 12
        elif hour_val == 0:
            hour_val = 12

        output = []
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        # For times to get displayed correctly, the values MUST be converted to unicode
        # When Select builds a list of options, it checks against Unicode values
        hour_val = u"%.2d" % hour_val
        minute_val = u"%.2d" % minute_val

        hour_choices = [("%.2d" % i, "%.2d" % i) for i in self.hours]
        local_attrs = self.build_attrs(id=self.hour_field % id_)
        select_html = Select(choices=hour_choices).render(self.hour_field % name, hour_val, local_attrs)
        output.append(select_html)

        minute_choices = [("%.2d" % i, "%.2d" % i) for i in self.minutes]
        local_attrs['id'] = self.minute_field % id_
        select_html = Select(choices=minute_choices).render(self.minute_field % name, minute_val, local_attrs)
        output.append(select_html)

        if self.twelve_hr:
            #  If we were given an initial value, make sure the correct meridiem gets selected.
            if self.meridiem_val is not None and self.meridiem_val.startswith('p'):
                meridiem_choices = [('p.m.', 'p.m.'), ('a.m.', 'a.m.')]
            else:
                meridiem_choices = [('a.m.', 'a.m.'), ('p.m.', 'p.m.')]

            local_attrs['id'] = local_attrs['id'] = self.meridiem_field % id_
            select_html = Select(choices=meridiem_choices).render(self.meridiem_field % name, self.meridiem_val,
                                                                  local_attrs)
            output.append(select_html)

        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_hour' % id_

    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        # if there's not h:m:s data, assume zero:
        h = data.get(self.hour_field % name, 0)  # hour
        m = data.get(self.minute_field % name, 0)  # minute
        s = data.get(self.minute_field % name, 0)
        meridiem = data.get(self.meridiem_field % name, None)

        # NOTE: if meridiem is None, assume 24-hr
        if meridiem is not None:
            if meridiem.lower().startswith('p') and int(h) != 12:
                h = (int(h) + 12) % 24
            elif meridiem.lower().startswith('a') and int(h) == 12:
                h = 0

        if (int(h) == 0 or h) and m and s:
            return '%s:%s:%s' % (h, m, s)

        return data.get(name, None)


class SplitSelectDateTimeWidget(MultiWidget):
    """
    MultiWidget = A widget that is composed of multiple widgets.
    This class combines SelectTimeWidget and SelectDateWidget so we have something
    like SpliteDateTimeWidget (in django.forms.widgets), but with Select elements.
    """

    def __init__(self, attrs=None, hour_step=None, minute_step=None, twelve_hr=None, years=None):
        """ pass all these parameters to their respective widget constructors..."""
        widgets = (SelectDateWidget(attrs=attrs, years=years),
                   SelectTimeWidget(attrs=attrs, hour_step=hour_step, minute_step=minute_step, twelve_hr=twelve_hr))
        super(SplitSelectDateTimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]

    def format_output(self, rendered_widgets):
        """
        Given a list of rendered widgets (as strings), it inserts an HTML
        linebreak between them.

        Returns a Unicode string representing the HTML for the whole lot.
        """
        rendered_widgets.insert(-1, '<br/>')
        return u''.join(rendered_widgets)