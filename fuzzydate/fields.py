# $Id: fields.py 669 2011-12-12 16:34:48Z gnoel $
"""
Implements a fuzzy date field that allows storage of inprecise date values like
"February 2008", "2009" or "3rd Quarter 2010".

It uses a second database column to store the "precision". This gives
potentially more flexibility when ordering, e.g. one could use SQL Functions to
make incomplete dates appear before or after the full dates.

About the implementation:

We want the precision field to be an implementation detail of the FuzzyDateField
class - the user shouldn't have to care about it in most cases. In essence, we
want our fuzzy date field to manage another field, and two database columns.
Consider this is not really something Django is architectured for, it works
surprisingly well. So, when FuzzyDateField's contribute_to_class method is
called, we use that opportunity to add the precision field as well.

Now, in cases where custom datatypes are needed, the docs recommend
SubfieldBase, which will call field.to_python() to convert a value from the
database into the custom type. This is such a case - we deal with FuzzyDate
instances. Unfortunately, we only get the value from the field's column itself
in the to_python() call - we don't have access to the precision field, so we
can't build a FuzzyDate instance. Note that fields have no reference to the
model they belong to.

However, we know that the precision field has already been loaded from the
database and must be somewhere, so let's see we if we can get access.

When Django is loading a model from the database, it sets an attribute on the
model instance for each field with the column value returned from the database
(as you know, the fields itself are stored in _meta.fields). For the default
field classes, we are really only dealing with basic python datatypes (
string, integer, datetime), which are returned by the database as-is. When a
custom datatype like our FuzzyDate comes in, the mentioned SubfieldBase
metaclass comes in. If your field class uses SubfieldBase as a metaclass, it
will ensure that the fields attribute on model instances is an object
implementing the descriptor protocol. It does this directly after the field was
registered with contribute_to_class. So when Django is then loading an object
from the database and tries to assign each value to the attributes, the
descriptor object can intercept that assignment. It then call's your fields
to_python() method and asks for a conversion.
Coincidentally, the descriptor has full access to the object instance via which
the attribute is accessed - in our case the model instance. This way, we'll be
able to access the precision field.

Unfortunately, SubfieldBase is not really open for customization - we have to
replace the entire fields.subclassing module. As we don't need to be generic
though, this is very simple. We just write a version of the descriptor class
used by SubfieldBase, that passes both the date and the precision values to
to_python (actually, we don't do this, we just let the descriptor class
itself do all the necessary work).

There is another problem though. Django goes though the fields in order and
sets attribute on the model instance after the other. We need to ensure that
when the date field's attribute is set, the hidden precision field has already
been set as well - in other words, the precision field must come *before* the
date field in the models _meta.fields list. Django's Field class uses a class
variable creation_counter that that is incremented for each field class
created - this is what fields are ordered by. Unfortunately, as the models
declared fields are created first by python, before Django's metaclass magic
begins which finally calls our contribute_to_class method. So any field we
create at this point will automatically appear after the date field itself (in
fact, after all the model's fields). This is were we have to employ our first
hack and modify the creation_counter of the precision field, so that it is put
at the right place.

TODO:
 * No support for many lookup types, including correct month, day or range
   lookups. They work, but on the internal date instance, without respecting
   the precision field. Not sure if this can even be done reasonably well.
 * In in and exact lookups will not exclude incomplete days either. Again, it
   doesn't appear as if this is something that will be easily doable.

"""

from django.db import models
from core import FuzzyDate, modifiers
import forms

__all__ = (
    'FuzzyDateField',
)

_precision_field_name = lambda name: "%s_precision"%name
_date_to_field_name = lambda name: "%s_to"%name
_date_mod_field_name = lambda name: "%s_mod"%name

class FuzzyDateCreator(object):
    """
    An equivalent to Django's default attribute descriptor class (enabled via
    the SubfieldBase metaclass, see module doc for details). However, instead
    of callig to_python() on our FuzzyDateField class, it stores the two
    different party of a fuzzy date, the date and the precision, separately, and
    updates them whenever something is assigned. If the attribute is read, it
    builds the FuzzyDate instance "on-demand" with the current data.
    """
    def __init__(self, field):
        self.field = field
        self.date_to_name = _date_to_field_name(self.field.name)
        self.date_mod_name = _date_mod_field_name(self.field.name)

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        date = obj.__dict__[self.field.name]
        if date is None: return None
        else:
            modifier = 0
            if (self.field.useModifier):
                modifier = getattr(obj, self.date_mod_name)
            return FuzzyDate(date, getattr(obj, self.date_to_name), modifiers.getElement(modifier))

    def __set__(self, obj, value):
        if isinstance(value, FuzzyDate):
            # fuzzy date is assigned: take over it's values
            obj.__dict__[self.field.name] = value.getDateFrom()
            setattr(obj, self.date_to_name, value.getDateTo())
            if (self.field.useModifier):
                setattr(obj, self.date_mod_name, value.getModifier().id)
        else:
            # standard python date: use the date portion and reset precision
            obj.__dict__[self.field.name] = self.field.to_python(value)
            # you could be tempted to reset the precision to "day" whenever
            # a user assigns a plain date - however, don't do this. when django
            # assigns to this while loading a row from the database, we want
            # to keep the precision that was already set!

class FuzzyDateField(models.DateField):
    
    useModifier = False
    
    def __init__(self, *args, **kwargs):
        if ('modifier' in kwargs):
            self.useModifier = (kwargs['modifier'] == True)
            # remove it from the kwargs otherwise the DateField will scream in horror.
            del kwargs['modifier']
        # add help line to the help_text
        if not kwargs.has_key('help_text'):
            kwargs['help_text'] = ur''
        else:
            kwargs['help_text'] += '<br/>'
        kwargs['help_text'] += ur'''Date format: dd-mm-yyyy. e.g. '25-10-1970' (on that day), '10-1970' (sometime that month) or '1970' (sometime that year). <br/> Date ranges: e.g. '1970 to 1975' (started in 1970 and finished in 1975). <br/> Uncertainty: e.g. 'c. 1972' (circa 1972), '?1972' (probably in 1972 but might be another year), '?1970 to 1975' (sometime between 1970 and 1975).'''
        models.DateField.__init__(self, *args, **kwargs)
    
    """
    A field that stores a fuzzy date. See the module doc for more information.
    """
    def contribute_to_class(self, cls, name):
        # first, create a hidden "precision" field. It is *crucial* that this
        # field appears *before* the actual date field (i.e. self) in the
        # models _meta.fields - to achieve this, we need to change it's
        # creation_counter class variable.
        date_to = models.DateField(editable=False, null=True, blank=True)
        # setting the counter to the same value as the date field itself will
        # ensure the precision field appear first - it is added first after all,
        # and when the date field is added later, it won't be sorted before it.
        date_to.creation_counter = self.creation_counter
        cls.add_to_class(_date_to_field_name(name), date_to)

        if (self.useModifier):
            # first, create a hidden "precision" field. It is *crucial* that this
            # field appears *before* the actual date field (i.e. self) in the
            # models _meta.fields - to achieve this, we need to change it's
            # creation_counter class variable.
            date_modifier = models.SmallIntegerField(null=False, default=0, blank=False, editable=False)
            # setting the counter to the same value as the date field itself will
            # ensure the precision field appear first - it is added first after all,
            # and when the date field is added later, it won't be sorted before it.
            date_modifier.creation_counter = self.creation_counter
            cls.add_to_class(_date_mod_field_name(name), date_modifier)
        
        # add the date field as normal
        super(FuzzyDateField, self).contribute_to_class(cls, name)

        # as we are not using SubfieldBase (see intro), we need to do it's job
        # ourselfs. we don't need to be generic, so don't use a metaclass, but
        # just assign the descriptor object here.
        setattr(cls, self.name, FuzzyDateCreator(self))

    def get_db_prep_save(self, value):
        if isinstance(value, FuzzyDate): value = value.getDateFrom()
        return super(FuzzyDateField, self).get_db_prep_save(value)

    # todo: GN
    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            return [self.get_db_prep_save(value)]
        elif lookup_type == 'in':
            return [self.get_db_prep_save(v) for v in value]
        else:
            # let the base class deal with the rest; some will work out fine,
            # like 'year', others will probably give unexpected results,
            # like 'range'.
            return super(FuzzyDateField, self).get_db_prep_lookup(lookup_type, value)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FuzzyDateField}
        defaults.update(kwargs)
        return super(FuzzyDateField, self).formfield(**defaults)

    # GN: overrided this function to prevent crash in Django 1.2+
    # It used to work without it in Django 1.1.
    # This is a kind of a hack as I didn't have the time to look into the reason for this bug.  
    # TODO: test it back in Django 1.1
    def to_python(self, value):
        param = value
        if param is not None and isinstance(param, FuzzyDate):
            param = param.getDateFrom()
        return super(FuzzyDateField, self).to_python(param)
    
    def get_internal_type(self):
        return "DateField"

    # Although we need flatten_data for (oldforms) admin, we don't need to
    # implement it here, as the DateField baseclass will just call strftime on
    # our FuzzyDate object, which is something we support.
