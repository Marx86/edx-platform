import datetime
from collections import OrderedDict
from csv import DictReader
import json
import pytz
import tablib
from urlparse import urljoin

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.context_processors import csrf
from django.template.loader import render_to_string
from django.urls import reverse
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from rest_framework import generics, viewsets

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.utils import generate_password
from student.models import CourseEnrollment
from student.helpers import get_next_url_for_login_page, do_create_account

from .forms import (
    StudentEnrollForm,
    StudentImportForm,
    StudentImportRegisterForm,
    InstructorProfileImportForm,
    get_tedix_registration_form,
    AccountImportValidationForm,
)
from .models import StudentProfile, StudentCourseDueDate, City, School
from .serializers import CitySerializer, SchoolSerilizer, SingleCitySerializer, SingleSchoolSerilizer


def manage_courses(request):
    InstructorProfile = apps.get_model('tedix_ro', 'InstructorProfile')
    user = request.user
    if not user.is_authenticated():
        return redirect(get_next_url_for_login_page(request))

    if not (user.is_staff or user.is_superuser):
        return redirect(reverse('dashboard'))

    context = {
        "csrftoken": csrf(request)["csrf_token"],
        'show_dashboard_tabs': True
    }
    try:
        if user.is_superuser:
            students = StudentProfile.objects.filter(user__is_active=True)
        else:
            students = user.instructorprofile.students.filter(user__is_active=True)
    except InstructorProfile.DoesNotExist:
        students = StudentProfile.objects.none()

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    courses = CourseOverview.objects.filter(enrollment_end__gt=now, enrollment_start__lt=now)
    form = StudentEnrollForm(students=students, courses=courses)
    if request.method == 'POST':
        data = dict(
            courses = map(CourseKey.from_string, request.POST.getlist('courses')),
            students = request.POST.getlist('students'),
            due_date = request.POST.get('due_date'),
            send_to_students=request.POST.get('send_to_students'),
            send_to_parents=request.POST.get('send_to_parents'),
            send_sms=request.POST.get('send_sms')
        )
        form = StudentEnrollForm(data=data, courses=courses, students=students)
        if form.is_valid():
            for student in form.cleaned_data['students']:
                courses_list = []
                for course in form.cleaned_data['courses']:
                    due_date = form.cleaned_data['due_date']
                    CourseEnrollment.enroll_by_email(student.user.email, course.id)
                    StudentCourseDueDate.objects.update_or_create(
                        student=student,
                        course_id=course.id,
                        defaults={'due_date':form.cleaned_data['due_date']}
                    )
                    courses_list.append([
                        urljoin(settings.LMS_ROOT_URL, reverse('openedx.course_experience.course_home', kwargs={'course_id': course.id})),
                        course.display_name
                    ])
                    user_time_zone = student.user.preferences.filter(key='time_zone').first()
                    if user_time_zone:
                        user_tz = pytz.timezone(user_time_zone.value)
                        course_tz_due_datetime = pytz.UTC.localize(due_date.replace(tzinfo=None), is_dst=None).astimezone(user_tz)
                        context = {
                            'courses': courses_list,
                            'due_date': course_tz_due_datetime.strftime(
                                "%b %d, %Y, %H:%M %P {} (%Z, UTC%z)".format(user_time_zone.value.replace("_", " "))
                            )
                        }
                    else:
                        context = {
                            'courses': courses_list,
                            'due_date': '{} UTC'.format(due_date.astimezone(pytz.UTC).strftime('%b %d, %Y, %H:%M %P'))
                        }
                html_message = render_to_string(
                    'emails/student_enroll_email_message.html',
                    context
                )
                txt_message = render_to_string(
                    'emails/student_enroll_email_message.txt',
                    context
                )
                from_address = configuration_helpers.get_value(
                    'email_from_address',
                    settings.DEFAULT_FROM_EMAIL
                )
                recipient_list = []
                if form.cleaned_data['send_to_students']:
                    recipient_list.append(student.user.email)
                if form.cleaned_data['send_to_parents']:
                    recipient_list.append(student.parents.first().user.email)

                if recipient_list:
                    send_mail("Due Date", txt_message, from_address, recipient_list, html_message=html_message)
                
                if form.cleaned_data['send_sms']:
                    # sending sms logic to be here
                    pass
            messages.success(request, 'Successfully assigned.')
            return redirect(reverse('manage_courses'))

    context.update({
        'form': form
    })

    return render_to_response('manage_courses.html', context)


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    paginator = None
    pagination_class = None

    def get_serializer_class(self):
        if self.kwargs.get('pk'):
            return CitySerializer
        return SingleSchoolSerilizer


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = School.objects.all()
    paginator = None
    pagination_class = None

    def get_serializer_class(self):
        if self.kwargs.get('pk'):
            return SchoolSerilizer
        return SingleCitySerializer


def teacher_import(request):
    from .forms import InstructorImportValidationForm
    role = 'instructor'
    form = InstructorProfileImportForm(request.POST, request.FILES)
    context = {'form': form}
    if request.POST and form.is_valid():
        data = tablib.Dataset()
        error_rows_data = []
        valid_rows_data = []
        input_format = form.cleaned_data['input_format']
        import_file = form.cleaned_data['import_file']
        if input_format == 'json':
            data.json = import_file.read()
            ## add validate format
        if input_format == 'csv':
            data.csv = import_file.read()
            ## add validate format
        for i, row in enumerate(data.dict, 1):
            row['password'] = generate_password()
            row['role'] = role
            user_validation_form = AccountImportValidationForm(data=row, tos_required=False)
            errors = None
            profile_validation_form = InstructorImportValidationForm(data=row)
            ## add validate username
            if user_validation_form.is_valid() and profile_validation_form.is_valid():
                if profile_validation_form.user_exists():
                    profile_validation_form.update_profile()
                else:
                    do_create_account(user_validation_form, profile_validation_form)
                    profile_validation_form.status = 'created'
                row.pop('password')
                row.pop('role')
                valid_rows_data.append([i, profile_validation_form.status, row])
            else:
                errors = {}
                errors_key = user_validation_form.errors.keys() + profile_validation_form.errors.keys()
                errors.update(user_validation_form.errors)
                errors.update(profile_validation_form.errors)
                row.pop('password')
                row.pop('role')
                error_rows_data.append([i, row, errors_key, errors])
        context.update({
            'error_rows_data': error_rows_data,
            'valid_rows_data': valid_rows_data,
            'headers': row.keys() ## dataset.headers
        })
    return render(request, 'teacher_import.html', context)

def students_import(request):
    import_form = StudentImportForm()
    errors_list = []
    headers = [
        'email',
        'public_name',
        'username',
        'phone',
        'parent_phone',
        'parent_email',
        'city',
        'school',
        'teacher_email',
        'classroom',
    ]
    context = {
        'import_form': import_form,
        'errors_list': errors_list,
        'site_header': 'LMS Administration'
    }
    if request.method == 'POST':
        import_form = StudentImportForm(request.POST, request.FILES)
        if import_form.is_valid():
            if import_form.cleaned_data['format'] == 'csv':
                dataset = DictReader(import_form.cleaned_data['file_to_import'])
            if import_form.cleaned_data['format'] == 'json':
                dataset = json.loads(import_form.cleaned_data['file_to_import'].read())
            role = 'student'
            for i, row in enumerate(dataset, 1):
                errors = {}
                form_data = {StudentImportRegisterForm.form_fields_map.get(k, k):v for k,v in row.items()}
                form_data['role'] = role
                form_data['password'] = User.objects.make_random_password()
                print(form_data)
                user_form = AccountImportValidationForm(form_data, tos_required=False)
                student_profile_form = StudentImportRegisterForm(form_data)
                state = 'new'
                if user_form.is_valid() and student_profile_form.is_valid():
                    if student_profile_form.exists(form_data):
                        state = student_profile_form.update(form_data)
                    else:
                        user, profile, registration = do_create_account(user_form, student_profile_form)
                else:
                    state = 'error'
                    errors.update(dict(user_form.errors.items()))
                    errors.update(dict(student_profile_form.errors.items()))
                errors_list.append((i, errors, state, row))
        context.update(dict(
            row_headers=headers
        ))
    return render(request, 'students_import.html', context)
