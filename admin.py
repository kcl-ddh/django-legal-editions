from django.contrib import admin


from legal_editions import models as edition_models


class EditionsInline (admin.TabularInline):

    model = edition_models.Edition.editors.through
    verbose_name = 'Edited Edition'
    verbose_name_plural = 'Edited Editions'


class EditorsInline (admin.TabularInline):

    model = edition_models.Edition.editors.through
    verbose_name = 'Editor'
    verbose_name_plural = 'Editors'


class HyparchetypeInline (admin.TabularInline):

    model = edition_models.Hyparchetype


class TextAttributeInline (admin.TabularInline):

    model = edition_models.Work.text_attributes.through
    verbose_name = 'Work-Text Attribute Relationship'
    verbose_name_plural = 'Work-Text Attribute relationships'


class VersionLanguagesInline (admin.TabularInline):

    model = edition_models.Version.languages.through


class WitnessInline (admin.TabularInline):

    model = edition_models.Version.witnesses.through


class WitnessLanguagesInline (admin.TabularInline):

    model = edition_models.Witness.languages.through


class WitnessTranscriptionInline (admin.TabularInline):

    model = edition_models.WitnessTranscription


class ArchiveAdmin (admin.ModelAdmin):

    pass


class EditionAdmin (admin.ModelAdmin):

    fieldsets = (
        (None, {'fields': ('abbreviation', 'version', 'date', 'status')}),
        ('Introduction', {'fields': ('introduction',)}),
        ('Texts', {'fields': ('text', 'translation')}),
        ('Further information', {'fields': ('internal_notes',)}),)
    inlines = [EditorsInline, HyparchetypeInline, WitnessTranscriptionInline]


class EditorAdmin (admin.ModelAdmin):

    fieldsets = (
        ('Name', {'fields': ('abbreviation', 'last_name', 'first_name')}),)
    list_display = ('id', 'abbreviation', 'last_name', 'first_name')
    list_display_links = list_display
    ordering = ('last_name',)
    inlines = [EditionsInline]
    search_fields = list_display


class HyparchetypeAdmin (admin.ModelAdmin):

    pass


class ManuscriptAdmin (admin.ModelAdmin):

    fieldsets = (
        ('Sigla', {'fields': ('sigla', 'sigla_provenance')}),
        ('Archive', {'fields': ('archive', 'shelf_mark')}),
        ('Others', {'fields': ('description', 'hide_from_listings',
                               'checked_folios', 'single_sheet',
                               'standard_edition')}))
    list_display = ('id', 'sigla', 'shelf_mark', 'archive', 'single_sheet')
    list_display_links = list_display
    list_filter = ('single_sheet', 'hide_from_listings', 'checked_folios',
                   'sigla_provenance', 'archive')
    ordering = ('archive', 'shelf_mark')
    search_fields = ('id', 'shelf_mark', 'sigla')


class VersionAdmin (admin.ModelAdmin):

    fieldsets = (
        ('Info', {'fields': ('standard_abbreviation', 'slug', 'name', 'work',
                             'date')}),
        ('Synopsis', {'fields': ('synopsis', 'synopsis_manuscripts',
                                 'print_editions')}))
    inlines = [VersionLanguagesInline, WitnessInline]
    list_display = ('id', 'standard_abbreviation', 'slug', 'get_name')
    list_display_links = list_display
    ordering = ('standard_abbreviation',)
    readonly_fields = ('slug',)
    search_fields = ('id', 'standard_abbreviation')


class VersionRelationshipAdmin (admin.ModelAdmin):

    fieldsets = ((None, {'fields': ('relationship_type', 'source', 'target',
                                    'description')}),)


class WitnessAdmin (admin.ModelAdmin):

    fieldsets = (
        ('Work', {'fields': ('work',)}),
        ('Location', {'fields': ('manuscript', 'range_start', 'range_end',
                                 'page')}),
        ('Description', {'fields': ('description',)}),)
    inlines = [WitnessLanguagesInline, WitnessInline]
    list_display = ('id', 'work', 'manuscript', 'range_start', 'range_end')
    list_display_links = list_display
    ordering = ('work',)
    search_fields = ('id', 'range_start', 'range_end')


class WorkAdmin (admin.ModelAdmin):

    fieldsets = ((None, {'fields': ('name', 'king', 'date')}),)
    inlines = [TextAttributeInline]
    list_display = ('id', 'name')
    list_display_links = list_display
    list_filter = ['text_attributes']


admin.site.register(edition_models.Archive, ArchiveAdmin)
admin.site.register(edition_models.Edition, EditionAdmin)
admin.site.register(edition_models.EditionStatus)
admin.site.register(edition_models.Editor, EditorAdmin)
admin.site.register(edition_models.FolioSide)
admin.site.register(edition_models.Hyparchetype, HyparchetypeAdmin)
admin.site.register(edition_models.King)
admin.site.register(edition_models.Language)
admin.site.register(edition_models.Manuscript, ManuscriptAdmin)
admin.site.register(edition_models.Person)
admin.site.register(edition_models.TextAttribute)
admin.site.register(edition_models.Version, VersionAdmin)
admin.site.register(edition_models.VersionRelationship,
                    VersionRelationshipAdmin)
admin.site.register(edition_models.VersionRelationshipType)
admin.site.register(edition_models.Witness, WitnessAdmin)
admin.site.register(edition_models.Work, WorkAdmin)
