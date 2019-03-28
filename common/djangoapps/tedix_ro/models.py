from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.core.validators import RegexValidator
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from student.models import AUDIT_LOG

CLASSROOM_CHOICES = (
    ('', ''),

    ('7A', '7A'),
    ('7B', '7B'),
    ('7C', '7C'),
    ('7D', '7D'),

    ('8A', '8A'),
    ('8B', '8B'),
    ('8C', '8C'),
    ('8D', '8D'),
)

phone_validator = RegexValidator(regex=r'^\d{10,15}$', message='Phone length should be from 10 to 15')


class City(models.Model):
    name = models.CharField(max_length=254, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Cities'

    def __unicode__(self):
        return self.name


class School(models.Model):
    name = models.CharField(max_length=254, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='%(class)s', on_delete=models.CASCADE)
    school_city = models.ForeignKey(City)
    school = models.ForeignKey(School)
    phone = models.CharField(_('phone'), validators=[phone_validator], max_length=15)

    class Meta:
        abstract = True

    def __unicode__(self):
        return unicode(self.user)


class InstructorProfile(UserProfile):
    """
    Related model for instructor profile
    """
    pass


class StudentProfile(UserProfile):
    """
    Related model for student profile
    """
    instructor = models.ForeignKey(InstructorProfile, related_name='students', null=True, on_delete=models.SET_NULL)
    classroom = models.CharField(_('classroom'), choices=CLASSROOM_CHOICES, max_length=254)

    def __unicode__(self):
        return unicode(self.user)

    def save(self, *args, **kwargs):
        super(StudentProfile, self).save(*args, **kwargs)

        # If this attribute is here, other needed fields are passed as well
        # These attrs are passed from tedix_ro.forms.StudentRegisterForm manually
        if getattr(self, 'parent_user', None):
            parent_profile = ParentProfile(
                user=self.parent_user,
                school_city=self.school_city,
                school=self.school,
                phone=self.parent_phone,
                password=self.password
            )
            parent_profile.save()
            parent_profile.students.add(self)


class ParentProfile(UserProfile):
    """
    Related model for parent profile
    """
    students = models.ManyToManyField(StudentProfile, related_name='parents')
    password = models.CharField(max_length=10) # it only nedeed for the first registration to send it with an activation email

    def __unicode__(self):
        return unicode(self.user)


@receiver(user_logged_in)
def student_parent_logged_in(sender, request, user, **kwargs):  # pylint: disable=unused-argument
    """
    Relogin as student when parent logins successfully
    """
    try:
        parent_profile = getattr(user, 'parentprofile', None)
        AUDIT_LOG.info(u'Parent Login success - {0} ({1})'.format(user.username, user.email))
        student = parent_profile.students.first() if parent_profile else None
        if student is not None and student.user.is_active:
            login(request, student.user, backend=settings.AUTHENTICATION_BACKENDS[0])
            AUDIT_LOG.info(u'Relogin as parent student - {0} ({1})'.format(student.user.username, student.user.email))
    except ParentProfile.DoesNotExist:
        pass
