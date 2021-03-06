from django.contrib.auth.models import User
from django.db import models
from utils.mixins import TranslatedModelMixin
import pytz

class VideoUpload(models.Model):
    user = models.ForeignKey(User)
    video = models.FileField(upload_to='video_uploads')
    created_at = models.DateTimeField(auto_now=True)

class Note(models.Model):
    user = models.ForeignKey(User)
    video = models.ForeignKey(VideoUpload)
    mark = models.IntegerField()
    comment = models.CharField(max_length=255)

class Agency(models.Model):
    name = models.CharField(max_length=500)
    class Meta:
        verbose_name_plural = "Agencies"
class Profile(models.Model):
    user = models.OneToOneField(User)
    agency = models.ForeignKey(Agency)
    higher_up = models.ForeignKey('self', blank=True, null=True)
    LANGS = (
        ('en', 'English'),
        ('es', 'Spanish'),
    )
    language = models.CharField(max_length=2,choices=LANGS)

    TYPES = (
        ('P', 'Participant'),
        ('C', 'Coach'),
        ('T', 'Trainer/Consultant'),
    )
    type = models.CharField(max_length=1, choices=TYPES, default='P')
    coach_welcome_video = models.FileField(upload_to = u'coach_video/', max_length=255, null=True, blank=True)

    TIMEZONES = [(tz,tz) for tz in pytz.all_timezones]
    timezone = models.CharField(max_length=100, choices=TIMEZONES, default='US/Pacific')
    def is_with(self, profile):
        """
            This function determines if a user is associated with another user.
            It does this by examining the tree structure of Profile. For
            example, in the tree below... T is with C1, C1 is not with C2,
            T is with P3, C2 is not with P1, etc.

                 T
                / \___
               C1      \
               |        C2
               P1      /  \
                      P2   P3

            Usage:
                    P1.is_with(C1)
                    >>> True
                    P2.is_with(P3)
                    >>> False
                    P3.is_with(T)
                    >>> True
        """
        me = self
        you = profile

        hu = me.higher_up
        while hu is not None:
            if hu == you:
                return True
            else:
                hu = hu.higher_up
        hu = you.higher_up
        while hu is not None:
            if hu == me:
                return True
            else:
                hu = hu.higher_up

        return False

class Message(models.Model):
    recipient = models.ForeignKey(User,related_name='msg_recipient')
    sender = models.ForeignKey(User,related_name='msg_sender')
    text = models.TextField()
    seen_by_recipient = models.BooleanField(default=False)
    def __unicode__(self):
        return self.text

class Star(models.Model):
    value = models.IntegerField()
    recipient = models.ForeignKey(User,related_name='str_recipient')
    sender = models.ForeignKey(User,related_name='str_sender')

class PageVisit(models.Model):
    user = models.IntegerField(null=True)
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now=True)

class Error(models.Model):
    user = models.ForeignKey(User)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

class ClinicalNote(models.Model):
    pass

class Level(models.Model, TranslatedModelMixin):
    title = models.CharField(max_length=255)
    es_title = models.CharField(max_length=255)
    position = models.IntegerField(default=1, help_text='What level/session is this?')
    language_code = 'en'
    translated_fields = ['title']
    class Meta:
        ordering = ('position',)

class Section(models.Model, TranslatedModelMixin):
    title = models.CharField(max_length=255)
    es_title = models.CharField(max_length=255)
    language_code = 'en'
    translated_fields = ['title']

class Page(models.Model, TranslatedModelMixin):
    level = models.ForeignKey(Level)
    section = models.ForeignKey(Section)
    title = models.CharField(max_length=255)
    html = models.TextField()
    display_welcome_video = models.BooleanField(default=False, help_text="By checking this the user will see their higher_up's welcome video if available.")
    es_title = models.CharField(max_length=255)
    es_html  = models.TextField()
    language_code = 'en'
    translated_fields = ['title', 'html']

class Edge(models.Model):
    u = models.ForeignKey(Page,related_name='from_page')
    v = models.ForeignKey(Page,related_name='to_page')

class Permission(models.Model):
    page = models.ForeignKey(Page)
    user = models.ForeignKey(User)

class Media(models.Model):
    file = models.FileField(upload_to = u'uploads/')

class Tip(models.Model, TranslatedModelMixin):
    text = models.CharField(max_length=255)
    es_text = models.CharField(max_length=255)
    language_code = 'en'
    translated_fields = ['text']

class CustomPage(models.Model, TranslatedModelMixin):
    html = models.TextField()
    es_html = models.TextField()
    language_code = 'en'
    translated_fields = ['html']

class Question(models.Model, TranslatedModelMixin):
    page = models.ForeignKey(Page)
    text = models.CharField(max_length=1000,blank=False)
    TYPES = (
        ('ra', 'radio'),
        ('ch', 'checkbox'),
        ('tx', 'text'),
    )
    type = models.CharField(max_length=2,choices=TYPES)
    is_scoreable = models.BooleanField(default=True,help_text="Will the answer to this question be scored?")
    position = models.IntegerField()

    es_text = models.CharField(max_length=1000,blank=False)
    language_code = 'en'
    translated_fields = ['text']
    class Meta:
        ordering = ['position']

class Choice(models.Model, TranslatedModelMixin):
    question = models.ForeignKey(Question)
    text = models.CharField(max_length=1000,blank=False)
    feedback = models.CharField(max_length=1000,blank=True)
    correct = models.BooleanField(blank=False,default=False,help_text="Is this a correct answer?")
    position = models.IntegerField()

    es_text = models.CharField(max_length=1000,blank=False)
    es_feedback = models.CharField(max_length=1000,blank=True)
    language_code = 'en'
    translated_fields = ['text']
    class Meta:
        ordering = ['position']

class Response(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question)
    choices = models.CommaSeparatedIntegerField(max_length=255)
    free = models.TextField()
    attempt = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now=True)

    @property
    def selected(self):
        if len(self.choices > 0):
            choice_pks = self.choices.split(',')
            choices = Choice.objects.filter(pk__in=choice_pks.split(','))
            return choices
        else:
            return None

    @property
    def correct(self):
        all_correct = False
        correct_answers = Choice.objects.filter(question=self.question, correct=True)
        if list(self.selected) == list(correct_answers):
            all_correct = True
        return all_correct

"""
    Home Visitor Curriculum.
"""
class HVTip(Tip):
    class Meta:
        verbose_name = "Coach Tip"
        verbose_name_plural = "Coach Tips"
class HVCustomPage(CustomPage):
    class Meta:
        verbose_name = "Coach CustomPage"
        verbose_name_plural = "Coach CustomPages"
class HVLevel(Level):
    class Meta:
        verbose_name = "Coach Level"
        verbose_name_plural = "Coach Levels"
class HVSection(Section):
    class Meta:
        verbose_name = "Coach Section"
        verbose_name_plural = "Coach Sections"

class HVPage(models.Model, TranslatedModelMixin):
    level = models.ForeignKey(HVLevel)
    section = models.ForeignKey(HVSection)
    title = models.CharField(max_length=255)
    html = models.TextField()
    display_welcome_video = models.BooleanField(default=False, help_text="By checking this the user will see their higher_up's welcome video if available.")
    es_title = models.CharField(max_length=255)
    es_html  = models.TextField()
    language_code = 'en'
    translated_fields = ['title', 'html']
    class Meta:
        verbose_name = "Coach Page"
        verbose_name_plural = "Coach Pages"

class HVEdge(models.Model):
    u = models.ForeignKey(HVPage,related_name='hv_from_page')
    v = models.ForeignKey(HVPage,related_name='hv_to_page')
    class Meta:
        verbose_name = "Coach Edge"
        verbose_name_plural = "Coach Edges"

class HVPermission(models.Model):
    page = models.ForeignKey(HVPage)
    user = models.ForeignKey(User)
    class Meta:
        verbose_name = "Coach Permission"
        verbose_name_plural = "Coach Permissions"

class HVQuestion(models.Model, TranslatedModelMixin):
    page = models.ForeignKey(HVPage)
    text = models.CharField(max_length=1000,blank=False)
    TYPES = (
        ('ra', 'radio'),
        ('ch', 'checkbox'),
        ('tx', 'text'),
    )
    type = models.CharField(max_length=2,choices=TYPES)
    is_scoreable = models.BooleanField(default=True,help_text="Will the answer to this question be scored?")
    position = models.IntegerField()

    es_text = models.CharField(max_length=1000,blank=False)
    language_code = 'en'
    translated_fields = ['text']
    class Meta:
        ordering = ['position']
        verbose_name = "Coach Question"
        verbose_name_plural = "Coach Questions"

class HVChoice(models.Model, TranslatedModelMixin):
    question = models.ForeignKey(HVQuestion)
    text = models.CharField(max_length=1000,blank=False)
    feedback = models.CharField(max_length=1000,blank=True)
    correct = models.BooleanField(blank=False,default=False,help_text="Is this a correct answer?")
    position = models.IntegerField()

    es_text = models.CharField(max_length=1000,blank=False)
    es_feedback = models.CharField(max_length=1000,blank=True)
    language_code = 'en'
    translated_fields = ['text']
    class Meta:
        ordering = ['position']
        verbose_name = "Coach Choice"
        verbose_name_plural = "Coach Choices"

class HVResponse(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(HVQuestion)
    choices = models.CommaSeparatedIntegerField(max_length=255)
    free = models.TextField()
    attempt = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Coach Response"
        verbose_name_plural = "Coach Responses"
    @property
    def selected(self):
        if len(self.choices > 0):
            choice_pks = self.choices.split(',')
            choices = Choice.objects.filter(pk__in=choice_pks.split(','))
            return choices
        else:
            return None

    @property
    def correct(self):
        all_correct = False
        correct_answers = Choice.objects.filter(question=self.question, correct=True)
        if list(self.selected) == list(correct_answers):
            all_correct = True
        return all_correct
