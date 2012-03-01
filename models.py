from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify

from fuzzydate import FuzzyDateField


class Archive (models.Model):

    """Stores details of an archive that holds manuscripts."""

    name = models.CharField(max_length=128)
    city = models.CharField(max_length=128)
    country = models.CharField(blank=True, max_length=128)

    class Meta:
        ordering = ['name', 'city']
        unique_together = (('city', 'name'),)

    def __unicode__ (self):
        return u'%s (%s)' % (self.name, self.city)


class Commentary (models.Model):

    """Stores user-submitted commentary on a particular part of an
    :model:`legal_editions.Edition`. Related to :model:`auth.User`."""

    text = models.TextField()
    user = models.ForeignKey(User, help_text='User (editor or registered user) who submitted this comment.')
    element_id = models.CharField(blank=True, max_length=32)
    updated = models.DateTimeField(blank=True, null=True)
    sort_order = models.IntegerField(blank=True, null=True)
    edition = models.ForeignKey('Edition')

    class Meta:
        verbose_name_plural = 'Commentaries'

    def __unicode__ (self):
        return 'Commentary by %s on %s in %s' % (self.user, self.element_id,
                                                 self.edition)


class Edition (models.Model):

    date = FuzzyDateField(blank=True, modifier=True, null=True)
    text = models.TextField(blank=True)
    translation = models.TextField(blank=True)
    abbreviation = models.CharField(max_length=32)
    internal_notes = models.TextField(blank=True, help_text='Internal notes associated with this edition. They will not appear on the website.')
    introduction = models.TextField(blank=True)
    editors = models.ManyToManyField('Editor')
    status = models.ForeignKey('EditionStatus')
    version = models.ForeignKey('Version')

    def get_editors (self):
        return self.editors.all()

    def get_introduction (self):
        introduction = self.introduction or self.version.synopsis
        return introduction

    def __unicode__ (self):
        return u'%s (%s)' % (self.abbreviation, self.version.get_name())


class EditionStatus (models.Model):

    """Stores a status of an edition, such as "draft" or "published"."""

    name = models.CharField(max_length=32, unique=True)

    class Meta:
        verbose_name_plural = 'Edition Statuses'

    def __unicode__ (self):
        return self.name


class Editor (models.Model):

    """Stores the name and abbreviation of an editor."""

    first_name = models.CharField(blank=True, max_length=32)
    last_name = models.CharField(blank=True, max_length=32)
    abbreviation = models.CharField(max_length=32, unique=True)


class FolioImage (models.Model):

    filename = models.CharField(max_length=128)
    filepath = models.CharField(max_length=128, unique=True)
    batch = models.CharField(blank=True, max_length=32)
    folio_number = models.CharField(blank=True, help_text='Folio number. Leavy empty if unknown. Do not include r/v information.', max_length=8)
    page = models.CharField(blank=True, help_text='Archive page number. Leave empty if not available.', max_length=8)
    display_order = models.IntegerField(blank=True, help_text='Optional. This number indicates in which order this folio will appear in a sequential reading of the manuscript. The value is relative to the display order of the other folio images.', null=True)
    internal_notes = models.TextField(blank=True)
    path = models.CharField(blank=True, max_length=128)
    filename_sort_order = models.IntegerField(blank=True, null=True)
    archived = models.BooleanField()
    manuscript = models.ForeignKey('Manuscript')
    folio_side = models.ForeignKey('FolioSide')

    def __unicode__ (self):
        return self.filepath


class FolioSide (models.Model):

    name = models.CharField(max_length=32, unique=True)

    def __unicode__ (self):
        return self.name


class Hyperarchetype (models.Model):

    sigla = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    edition = models.ForeignKey('Edition')

    def __unicode__ (self):
        return u'%s - %s' % (self.edition, self.sigla)


class Language (models.Model):

    """Stores a language."""

    name = models.CharField(max_length=32, unique=True)
    colour = models.CharField(blank=True, max_length=8)

    def __unicode__ (self):
        return self.name


class Manuscript (models.Model):

    """Stores details of a manuscript. Related to
    :model:`legal_editions.Archive` and
    :model:`legal_editions.SiglaProvenance`."""

    shelf_mark = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    sigla = models.CharField(blank=True, max_length=32)
    slug = models.SlugField(max_length=250)
    hide_from_listings = models.BooleanField()
    checked_folios = models.BooleanField(help_text='Tick this box if the facsimiles of this manuscript have been verified and are ready to be displayed on the public website.')
    single_sheet = models.BooleanField()
    hide_folio_numbers = models.BooleanField(help_text='Tick this box if the folio or page numbers should not appear on the website. To appear on the website, all folio images must have a folio or page number assigned to them in the datatabase. When the folios have no real/actual number this requirement forces you to provide abritrary numbers anyway. In that case, ticking this box will hide this arbitrary number on the site.')
    standard_edition = models.BooleanField(help_text='Tick this box if this document is a standard edition.')
    archive = models.ForeignKey('Archive')
    sigla_provenance = models.ForeignKey('SiglaProvenance', blank=True,
                                         null=True)

    def get_type_label (self):
        label = 'manuscript'
        if self.standard_edition:
            label = 'edition'
        return label

    def __save__ (self, *args, **kwargs):
        self.slug = slugify(self.sigla)
        super(Manuscript, self).save(*args, **kwargs)

    def __unicode__ (self):
        sigla = ''
        if self.sigla:
            sigla = ' (%s)' % self.sigla
        return u'%s%s' % (self.shelf_mark, sigla)


class Person (models.Model):
    
    name = models.CharField(max_length=128, unique=True)

    class Meta:
        verbose_name_plural = 'People'

    def __unicode__ (self):
        return self.name


class King (Person):

    """Stores details about a king, related when appropriate to a
    :model:`legal_editions.Work`."""

    beginning_regnal_year = FuzzyDateField(blank=True, modifier=True, null=True)
    end_regnal_year = FuzzyDateField(blank=True, modifier=True, null=True)


class SiglaProvenance (models.Model):

    name = models.CharField(max_length=32, unique=True)

    def __unicode__ (self):
        return self.name


class TextAttribute (models.Model):

    name = models.CharField(max_length=32, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Text Attribute'
        verbose_name_plural = 'Text Attributes'

    def __unicode__ (self):
        return self.name


class Version (models.Model):

    standard_abbreviation = models.CharField(max_length=32, unique=True)
    synopsis = models.TextField(blank=True)
    name = models.CharField(blank=True, help_text="Leave empty if the name is the same as the Work's name", max_length=128)
    slug = models.SlugField(max_length=250)
    print_editions = models.TextField(blank=True)
    synopsis_manuscripts = models.TextField(blank=True)
    date = FuzzyDateField(blank=True, modifier=True, null=True)
    graph = models.TextField(blank=True)
    work = models.ForeignKey('Work')
    witnesses = models.ManyToManyField('Witness')
    languages = models.ManyToManyField('Language')

    class Meta:
        ordering = ['standard_abbreviation']

    def get_languages (self):
        return self.languages.all()

    def get_name (self):
        name = self.name or self.work.name
        return name

    def get_witnesses (self):
        self.witness_set.all().order_by('manuscript__sigla')

    def __save__ (self, *args, **kwargs):
        self.slug = slugify(self.standard_abbreviation)
        super(Version, self).save(*args, **kwargs)

    def __unicode__ (self):
        return u'%s - %s' % (self.standard_abbreviation, self.get_name())


class VersionRelationship (models.Model):

    """Stores a directed relationship between two versions. Related to
    :model:`legal_editions.Version` and
    :model:`legal_editions.VersionRelationshipType`."""

    description = models.TextField(blank=True)
    source = models.ForeignKey('Version',
                               related_name='source_version_relationships')
    target = models.ForeignKey('Version',
                               related_name='target_version_relationships')
    relationship_type = models.ForeignKey('VersionRelationshipType')


class VersionRelationshipType (models.Model):

    """Stores a type of relationship between versions."""

    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)

    def __unicode__ (self):
        return self.name


class Witness (models.Model):

    """Stores details of a witness to a work in a manuscript. Related
    to :model:`legal_editions.Manuscript`,
    :model:`legal_editions.Work` and
    :model:`legal_editions.Language`."""

    range_start = models.CharField(blank=True, help_text="The page/folio number in the source document that correspond to the beginning of the text. (e.g. '10' or '30r').", max_length=8)
    range_end = models.CharField(blank=True, help_text="The page/folio number in the source document that correspond to the end of the text. (e.g. '15' or '41v').", max_length=8)
    description = models.TextField(blank=True)
    medieval_translation = models.BooleanField()
    page = models.BooleanField(help_text='Tick this box if the range is expressed in page numbers. Leave it unticked if the range is expressed in folio numbers.')
    hide_from_listings = models.BooleanField(help_text='Hide this witness from the manuscript listings on the webiste.')
    manuscript = models.ForeignKey('Manuscript')
    work = models.ForeignKey('Work')
    languages = models.ManyToManyField('Language')

    class Meta:
        verbose_name_plural = 'Witnesses'

    def get_languages (self):
        return self.languages.all()


class WitnessTranscription (models.Model):

    """Each witness transcription is associated with a particular
    edition, to allow an editor to make their own decisions."""

    witness = models.ForeignKey('Witness')
    edition = models.ForeignKey('Edition')
    transcription = models.TextField()
    translation = models.TextField(blank=True)

    class Meta:
        unique_together = (('witness', 'edition'),)

    def __unicode__ (self):
        return u'Transcription of %s' % self.witness.manuscript.sigla


class Work (models.Model):

    """A Work is an abstraction of a text, as divorced from any
    particular instance of that text."""

    name = models.CharField(max_length=128, unique=True)
    date = FuzzyDateField(blank=True, modifier=True, null=True)
    king = models.ForeignKey('King', blank=True, null=True)
    text_attributes = models.ManyToManyField('TextAttribute')

    class Meta:
        ordering = ['name']

    def get_attributes (self):
        return self.text_attributes.all()

    def __unicode__ (self):
        return self.name
