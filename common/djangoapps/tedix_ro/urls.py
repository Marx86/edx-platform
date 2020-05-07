from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from .views import (
    CityViewSet,
    SchoolViewSet,
    InstructorProfileImportView,
    StudentProfileImportView,
    VideoLessonViewSet,
    city_import,
    manage_courses,
    personal_due_dates,
    extended_report,
    report,
)

router = DefaultRouter()

router.register(r'cities', CityViewSet)
router.register(r'schools', SchoolViewSet)

urlpatterns = [
    url(r'^my_reports/$', report, name='my_reports'),
    url(r'^extended_report/(?P<course_key>[^/]*)/$', extended_report, name='extended_report'),
    url(r'^manage_courses$', manage_courses, name='manage_courses'),
    url(r'^personal_due_dates$', personal_due_dates, name='personal_due_dates'),
    url(r'^admin/tedix_ro/instructorprofile/import/$', InstructorProfileImportView.as_view(), name='teacher_import'),
    url(r'^admin/tedix_ro/studentprofile/import/$', StudentProfileImportView.as_view(), name='students_import'),
    url(r'^admin/tedix_ro/city/import/$', city_import, name='sities_import'),
    url(r'^api/', include(router.urls)),
    url(r'^api/video-lesson/?$', VideoLessonViewSet.as_view({'post': 'create', 'get': 'list'}), name='video-lesson')
]
