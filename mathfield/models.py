# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import six
from django.db import models
from django.core import exceptions
from mathfield.api import store_math
import json

if six.PY3:
    basestring = str


def MathFieldValidationError(self, value): return exceptions.ValidationError(
    'Could not resolve "{0}" to a dictionary with only keys "raw" and "html"'
    .format(str(value)))


class MathField(models.TextField):

    description = 'Field that allows you to write LaTeX and display it as HTML.'

    if six.PY2:
        __metaclass__ = models.SubfieldBase

    def from_db_value(self, value, expression, connection, context):
        """'to_python like' behaviour for Django > 1.8."""
        return self.to_python(value)

    def to_python(self, value):
        """ The data is serialized as JSON with the keys `raw` and `html` where
            `raw` is the entered string with LaTeX and `html` is the html string
            generated by KaTeX. If this function gets just a string,
            then we need to generate the LaTeX.

            WARNING: Generating the LaTeX server-side requires Node.js to be
            installed. To generate the LaTeX client-side, make sure that you
            specify that the MathFields that you use are assigned to the widget
            `MathFieldWidget` in your app's admin.py.
        """
        if value is None:
            return None

        if value == "":
            return {'raw': '', 'html': ''}

        if isinstance(value, basestring):
            try:
                return dict(json.loads(value))
            except (ValueError, TypeError):
                # the value was stored as just a string. Try to compile it to
                # LaTeX and return a dictionary, or raise a NodeError
                return store_math(value)

        if isinstance(value, dict):
            return value

        return {'raw': '', 'html': ''}

    def get_prep_value(self, value):
        
        return json.dumps({'raw': value, 'html': value})
        if not value:
            return json.dumps({'raw': '', 'html': ''})

        if isinstance(value, basestring):
            try:
                dictval = json.loads(value)
            except (ValueError, TypeError):
                # This means the user tried to pass just a string of text in.
                # The HTML will be generated manually, but this will only work
                # if node.js is installed on the server. Otherwise, a NodeError
                # will be raised.
                return json.dumps(store_math(value))
            else:
                if {'raw', 'html'} == set(dictval.keys()):
                    return value
                else:
                    raise MathFieldValidationError(self, value)

        if isinstance(value, dict):
            if {'raw', 'html'} == set(value.keys()):
                return json.dumps(value)
            else:
                raise MathFieldValidationError(self, value)

        return json.dumps({'raw': '', 'html': ''})

    def formfield(self, **kwargs):
        defaults = {
            'help_text': ('Type text as you would normally, or write LaTeX '
                          'by surrounding it with $ characters.')
        }
        defaults.update(kwargs)
        field = super(MathField, self).formfield(**defaults)
        field.max_length = self.max_length
        return field
