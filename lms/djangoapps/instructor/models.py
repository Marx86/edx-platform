"""
Module for instructor models.
"""
from collections import namedtuple

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from lms.djangoapps.instructor.access import allow_access
from openedx.core.djangoapps.course_groups.models import CourseUserGroup

Course = namedtuple('Course', ['id'])


class CohortAssigmentManager(models.Manager):
    def delete_assigned_cohorts(self, user):
        return self.get_queryset().filter(user=user).delete()


class CohortAssigment(models.Model):
    """
    Link between staff(user) and cohort.
    """

    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    cohort = models.ForeignKey(CourseUserGroup, db_index=True, on_delete=models.CASCADE)
    objects = CohortAssigmentManager()

    class Meta:
        app_label = 'instructor'
        unique_together = (('cohort', 'user'),)


@receiver(post_save, sender=CohortAssigment)
def allow_course_access_for_cohort_leader(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Send request to allow user access to course modification after the user is assigned as cohort leader of the course.
    """

    if created:
        course = Course(id=instance.cohort.course_id)
        user = instance.user
        allow_access(course, user, 'staff')
