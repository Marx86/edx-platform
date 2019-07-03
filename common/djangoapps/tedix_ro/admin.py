import datetime
from itertools import chain
import pytz
import time

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.models import User
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from import_export import resources, widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from import_export.formats import base_formats
from import_export.forms import ImportForm
from import_export.signals import post_import
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.user_api.accounts.utils import generate_password

from student.forms import AccountCreationForm
from student.helpers import do_create_account
from student.models import UserProfile
from tedix_ro.models import (
    City,
    School,
    ParentProfile,
    StudentProfile,
    InstructorProfile,
    Classroom,
    StudentCourseDueDate
)


admin.site.register(Classroom)


class ProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        instructors = InstructorProfile.objects.all()
        students = StudentProfile.objects.all()
        parents = ParentProfile.objects.all()
        instance = kwargs.get('instance')
        if instance:
            if isinstance(instance, StudentProfile):
                students = students.exclude(user=instance.user)
            if isinstance(instance, InstructorProfile):
                instructors = instructors.exclude(user=instance.user)
            if isinstance(instance, ParentProfile):
                parents = parents.exclude(user=instance.user)
        users = User.objects.exclude(id__in=set(chain(
            instructors.values_list('user_id', flat=True),
            students.values_list('user_id', flat=True),
            parents.values_list('user_id', flat=True)
        )))
        self.fields['user'].queryset = users


class StudentProfileForm(ProfileForm):
    class Meta:
        model = StudentProfile
        fields = '__all__'


class InstructorProfileForm(ProfileForm):
    class Meta:
        model = InstructorProfile
        fields = '__all__'


class ParentProfileForm(ProfileForm):
    class Meta:
        model = ParentProfile
        fields = '__all__'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    form = StudentProfileForm


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentProfileForm


class InstructorProfileImportForm(ImportForm):

    is_send_email = forms.BooleanField(label = "Send emails")

class InstructorProfileResource(resources.ModelResource):
    import_errors = []

    username = Field(
        attribute='user',
        column_name='username',
        widget=widgets.ForeignKeyWidget(User, 'username')
    )
    email = Field(
        attribute='user',
        column_name='email',
        widget=widgets.ForeignKeyWidget(User, 'email')
    )

    name = Field(
        attribute='user__profile__name',
        column_name='name',
    )

    class Meta:
        model = InstructorProfile
        fields = ('username', 'email', 'name', 'school_city', 'school', 'phone')
        import_id_fields = ('email',)
        skip_unchanged = True

    def before_import_row(self, row, **kwargs):
        """
        Override to add additional logic. Does nothing by default.
        """
        print('___________NEW_ROW!!!!!!!!!___________') 
        row['password'] = generate_password()
        print(row)
        form = AccountCreationForm(data=row, tos_required=False)
        self.import_errors = []
        if form.is_valid():
            do_create_account(form)
        else:
            self.import_errors.append(form.errors)
            print(self.import_errors)
        super(InstructorProfileResource, self).before_import_row(row, **kwargs)

    def after_import_row(self, row, row_result, **kwargs):
        """
        Override to add additional logic. Does nothing by default.
        """
        for error in self.import_errors:
            error_message = []
            for key in error:
                error_message.append('{} - {}'.format(key, ''.join(error[key])))
            row_result.errors.append(self.get_error_result_class()('', '\n'.join(error_message), row))

        super(InstructorProfileResource, self).after_import_row(row, row_result, **kwargs)


@admin.register(InstructorProfile)
class InstructorProfileAdmin(ImportExportModelAdmin):
    form = InstructorProfileForm
    resource_class = InstructorProfileResource
    formats = (
        base_formats.CSV,
        base_formats.JSON,
    )

    def get_import_form(self):
        return InstructorProfileImportForm
    

    # def add_error_message(self, result, request):
    #     for error in self.get_resource_class().import_errors:
    #         for key in error:
    #             messages.error(request, '{}. {}'.format(key, '\n'.join(error[key])))
    #     print(messages)


    def process_result(self, result, request):
        self.generate_log_entries(result, request)
        # self.add_error_message(result, request)
        self.add_success_message(result, request)
        post_import.send(sender=None, model=self.model)

        url = reverse('admin:%s_%s_changelist' % self.get_model_info())
        return HttpResponseRedirect(url)



class CityResource(resources.ModelResource):

    class Meta:
        model = City
        fields = ('name',)
        import_id_fields = ('name',)


@admin.register(City)
class CityAdmin(ImportExportModelAdmin):
    resource_class = CityResource
    formats = (
        base_formats.CSV,
        base_formats.JSON,
    )


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name',)


class CustomAdminSplitDateTime(AdminSplitDateTime):

    def decompress(self, value):
        if value:
            return [value.date(), value.time()]
        return [None, None]


class StudentCourseDueDateForm(forms.ModelForm):

    class Meta:
        model = StudentCourseDueDate
        fields = '__all__'
        help_texts = {
            'due_date': 'Time in UTC',
        }
    def __init__(self, *args, **kwargs):
        super(StudentCourseDueDateForm, self).__init__(*args, **kwargs)
        self.fields['due_date'].widget = CustomAdminSplitDateTime()
        self.fields['student'].queryset = StudentProfile.objects.filter(user__is_active=True)
    
    def clean_due_date(self):
        data = self.cleaned_data['due_date'].replace(tzinfo=pytz.UTC)
        return data

    def clean(self):
        super(StudentCourseDueDateForm, self).clean()
        student = self.cleaned_data.get('student')
        due_date_utc = self.cleaned_data.get('due_date')
        if due_date_utc and student:
            try:
                course_id = CourseKey.from_string(self.cleaned_data.get('course_id'))
                course = CourseOverview.objects.get(id=course_id)
                utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
                if not (course.start < due_date_utc < course.end and utcnow < due_date_utc):
                    self.add_error('due_date', 'This due date is not valid for the course: {}'.format(course_id))
            except CourseOverview.DoesNotExist:
                raise forms.ValidationError("Course does not exist")
            except InvalidKeyError:
                self.add_error('course_id', 'Invalid CourseKey')

        return self.cleaned_data


@admin.register(StudentCourseDueDate)
class StudentCourseDueDateAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_id', 'format_date')
    form = StudentCourseDueDateForm
    
    def format_date(self, obj):
        return obj.due_date.strftime('%d %b %Y %H:%M')
        
    format_date.short_description = 'Due Date (UTC)'
