"""
This file contains tasks that are designed to perform background operations on the
running state of a course.

"""
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from time import time

import json

import unicodecsv
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import DefaultStorage
from django.db.models import Q
from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
from openassessment.data import OraAggregateData
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.gating.api import get_required_content
from pytz import UTC, timezone
from xmodule.modulestore.django import modulestore

from certificates.models import GeneratedCertificate, CertificateStatuses
from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from instructor_analytics.basic import get_proctored_exam_results
from instructor_analytics.csvs import format_dictlist
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from survey.models import SurveyAnswer
from util.file import UniversalNewlineIterator

from .runner import TaskProgress
from .utils import UPDATE_STATUS_FAILED, UPDATE_STATUS_SUCCEEDED, upload_csv_to_report_store

# define different loggers for use within tasks and on client side
TASK_LOG = logging.getLogger('edx.celery.task')


def upload_course_survey_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a html report containing the survey results for a course.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    current_step = {'step': 'Gathering course survey report information'}
    task_progress.update_task_state(extra_meta=current_step)

    distinct_survey_fields_queryset = SurveyAnswer.objects.filter(course_key=course_id).values('field_name').distinct()
    survey_fields = []
    for unique_field_row in distinct_survey_fields_queryset:
        survey_fields.append(unique_field_row['field_name'])
    survey_fields.sort()

    user_survey_answers = OrderedDict()
    survey_answers_for_course = SurveyAnswer.objects.filter(course_key=course_id).select_related('user')

    for survey_field_record in survey_answers_for_course:
        user_id = survey_field_record.user.id
        if user_id not in user_survey_answers.keys():
            user_survey_answers[user_id] = {
                'username': survey_field_record.user.username,
                'email': survey_field_record.user.email
            }

        user_survey_answers[user_id][survey_field_record.field_name] = survey_field_record.field_value

    header = ["User ID", "User Name", "Email"]
    header.extend(survey_fields)
    csv_rows = []

    for user_id in user_survey_answers.keys():
        row = []
        row.append(user_id)
        row.append(user_survey_answers[user_id].get('username', ''))
        row.append(user_survey_answers[user_id].get('email', ''))
        for survey_field in survey_fields:
            row.append(user_survey_answers[user_id].get(survey_field, ''))
        csv_rows.append(row)

    task_progress.attempted = task_progress.succeeded = len(csv_rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    csv_rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(csv_rows, 'course_survey_results', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_proctored_exam_results_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):  # pylint: disable=invalid-name
    """
    For a given `course_id`, generate a CSV file containing
    information about proctored exam results, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about proctored exam results in a course'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = _task_input.get('features')
    student_data = get_proctored_exam_results(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'proctored_exam_results_report', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def cohort_students_and_upload(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    Within a given course, cohort students in bulk, then upload the results
    using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)

    # Iterate through rows to get total assignments for task progress
    with DefaultStorage().open(task_input['file_name']) as f:
        total_assignments = 0
        for _line in unicodecsv.DictReader(UniversalNewlineIterator(f)):
            total_assignments += 1

    task_progress = TaskProgress(action_name, total_assignments, start_time)
    current_step = {'step': 'Cohorting Students'}
    task_progress.update_task_state(extra_meta=current_step)

    # cohorts_status is a mapping from cohort_name to metadata about
    # that cohort.  The metadata will include information about users
    # successfully added to the cohort, users not found, Preassigned
    # users, and a cached reference to the corresponding cohort object
    # to prevent redundant cohort queries.
    cohorts_status = {}

    with DefaultStorage().open(task_input['file_name']) as f:
        for row in unicodecsv.DictReader(UniversalNewlineIterator(f), encoding='utf-8'):
            # Try to use the 'email' field to identify the user.  If it's not present, use 'username'.
            username_or_email = row.get('email') or row.get('username')
            cohort_name = row.get('cohort') or ''
            task_progress.attempted += 1

            if not cohorts_status.get(cohort_name):
                cohorts_status[cohort_name] = {
                    'Cohort Name': cohort_name,
                    'Learners Added': 0,
                    'Learners Not Found': set(),
                    'Invalid Email Addresses': set(),
                    'Preassigned Learners': set()
                }
                try:
                    cohorts_status[cohort_name]['cohort'] = CourseUserGroup.objects.get(
                        course_id=course_id,
                        group_type=CourseUserGroup.COHORT,
                        name=cohort_name
                    )
                    cohorts_status[cohort_name]["Exists"] = True
                except CourseUserGroup.DoesNotExist:
                    cohorts_status[cohort_name]["Exists"] = False

            if not cohorts_status[cohort_name]['Exists']:
                task_progress.failed += 1
                continue

            try:
                # If add_user_to_cohort successfully adds a user, a user object is returned.
                # If a user is preassigned to a cohort, no user object is returned (we already have the email address).
                (user, previous_cohort, preassigned) = add_user_to_cohort(cohorts_status[cohort_name]['cohort'], username_or_email)
                if preassigned:
                    cohorts_status[cohort_name]['Preassigned Learners'].add(username_or_email)
                    task_progress.preassigned += 1
                else:
                    cohorts_status[cohort_name]['Learners Added'] += 1
                    task_progress.succeeded += 1
            except User.DoesNotExist:
                # Raised when a user with the username could not be found, and the email is not valid
                cohorts_status[cohort_name]['Learners Not Found'].add(username_or_email)
                task_progress.failed += 1
            except ValidationError:
                # Raised when a user with the username could not be found, and the email is not valid,
                # but the entered string contains an "@"
                # Since there is no way to know if the entered string is an invalid username or an invalid email,
                # assume that a string with the "@" symbol in it is an attempt at entering an email
                cohorts_status[cohort_name]['Invalid Email Addresses'].add(username_or_email)
                task_progress.failed += 1
            except ValueError:
                # Raised when the user is already in the given cohort
                task_progress.skipped += 1

            task_progress.update_task_state(extra_meta=current_step)

    current_step['step'] = 'Uploading CSV'
    task_progress.update_task_state(extra_meta=current_step)

    # Filter the output of `add_users_to_cohorts` in order to upload the result.
    output_header = ['Cohort Name', 'Exists', 'Learners Added', 'Learners Not Found', 'Invalid Email Addresses', 'Preassigned Learners']
    output_rows = [
        [
            ','.join(status_dict.get(column_name, '')) if (column_name == 'Learners Not Found'
                                                           or column_name == 'Invalid Email Addresses'
                                                           or column_name == 'Preassigned Learners')
            else status_dict[column_name]
            for column_name in output_header
        ]
        for _cohort_name, status_dict in cohorts_status.iteritems()
    ]
    output_rows.insert(0, output_header)
    upload_csv_to_report_store(output_rows, 'cohort_results', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_ora2_data(
        _xmodule_instance_args, _entry_id, course_id, _task_input, action_name
):
    """
    Collect ora2 responses and upload them to S3 as a CSV
    """

    start_date = datetime.now(UTC)
    start_time = time()

    num_attempted = 1
    num_total = 1

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    task_progress = TaskProgress(action_name, num_total, start_time)
    task_progress.attempted = num_attempted

    curr_step = {'step': "Collecting responses"}
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s for all submissions',
        task_info_string,
        action_name,
        curr_step,
    )

    task_progress.update_task_state(extra_meta=curr_step)

    try:
        header, datarows = OraAggregateData.collect_ora2_data(course_id)
        rows = [header] + [row for row in datarows]
    # Update progress to failed regardless of error type
    except Exception:  # pylint: disable=broad-except
        TASK_LOG.exception('Failed to get ORA data.')
        task_progress.failed = 1
        curr_step = {'step': "Error while collecting data"}

        task_progress.update_task_state(extra_meta=curr_step)

        return UPDATE_STATUS_FAILED

    task_progress.succeeded = 1
    curr_step = {'step': "Uploading CSV"}
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s',
        task_info_string,
        action_name,
        curr_step,
    )
    task_progress.update_task_state(extra_meta=curr_step)

    upload_csv_to_report_store(rows, 'ORA_data', course_id, start_date)

    curr_step = {'step': 'Finalizing ORA data report'}
    task_progress.update_task_state(extra_meta=curr_step)
    TASK_LOG.info(u'%s, Task type: %s, Upload complete.', task_info_string, action_name)

    return UPDATE_STATUS_SUCCEEDED


def upload_course_certificates_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a html report containing the certificates data for a course.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    current_step = {'step': 'Gathering course certificates report information'}
    task_progress.update_task_state(extra_meta=current_step)

    course_overview = CourseOverview.get_from_id(course_id)
    header, csv_rows = get_certificates_report([course_overview])

    task_progress.attempted = task_progress.succeeded = len(csv_rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    csv_rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(csv_rows, 'course_certificates_report', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_all_courses_certificates_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    Generate a html report containing the certificates data for all courses.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    current_step = {'step': 'Gathering course certificates report information'}
    task_progress.update_task_state(extra_meta=current_step)

    courses = CourseOverview.objects.filter(Q(end__gte=start_date-timedelta(days=365)) | Q(end__isnull=True))

    header, csv_rows = get_certificates_report(courses)

    task_progress.attempted = task_progress.succeeded = len(csv_rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    csv_rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(csv_rows, 'all_courses_certificates_report', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def get_certificates_report(courses):
    header = ["Awarded Date: Date", "Certificate: Name", "Student: Full Name", "Student: Email",
              "User Certificate: Certificate Number", "User Certificate: Score",
              "Student: State Abbreviation", "User Student License Number: License Number"]
    csv_rows = []

    for course_overview in courses:

        generated_certificates = GeneratedCertificate.eligible_certificates.filter(
            course_id=course_overview.id,
            status=CertificateStatuses.downloadable
        )
        for generated_certificate in generated_certificates:
            row = []
            row.append(generated_certificate.created_date.astimezone(timezone(settings.TIME_ZONE)).strftime("%d/%m/%Y"))
            row.append(course_overview.display_name)

            if hasattr(generated_certificate.user, 'profile'):
                full_name = generated_certificate.user.profile.name
            else:
                full_name = generated_certificate.user.username

            row.append(full_name)
            row.append(generated_certificate.user.email)
            row.append(generated_certificate.verify_uuid)

            try:
                score = '{0:.0%}'.format(float(generated_certificate.grade))
            except (ValueError, TypeError):
                score = '0%'

            row.append(score)

            try:
                state_extra_infos = generated_certificate.user.extrainfo.stateextrainfo_set.all()
            except AttributeError:
                state_extra_infos = []

            for state_extra_info in state_extra_infos:
                row_copy = row[:]
                row_copy.append(state_extra_info.state)
                row_copy.append(state_extra_info.license)
                csv_rows.append(row_copy)

            if not state_extra_infos:
                csv_rows.append(row)

    return header, csv_rows


def upload_student_transcript_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    current_step = {'step': 'Gathering student progress report information'}
    task_progress.update_task_state(extra_meta=current_step)

    course = get_course_by_id(course_id, depth=4)
    user = User.objects.get(id=_task_input.get('user_id'))

    header, csv_rows = get_student_transcript_report(course, user)

    task_progress.attempted = task_progress.succeeded = len(csv_rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    csv_rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(csv_rows, 'student_transcript_report', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def get_student_transcript_report(course, user):
    header = ['Subsection', 'Question', 'Date', 'Attempts', 'Status', 'Percent']
    csv_rows = []
    required_contents = {}

    course_grade = CourseGradeFactory().create(user, course)
    courseware_summary = course_grade.chapter_grades.values()

    for chapter in courseware_summary:
        if not chapter['display_name'] == "hidden":
            for section in chapter['sections']:
                required_content, min_score = get_required_content(course.id, section.location)
                if required_content:
                    required_contents[required_content] = int(min_score) if min_score else 0

    for chapter in courseware_summary:
        if not chapter['display_name'] == "hidden":
            for section in chapter['sections']:
                row_sequential = [section.display_name, '', '', '']
                earned = section.all_total.earned
                total = section.all_total.possible
                percentage = int(float(earned) / total * 100) if earned > 0 and total > 0 else 0

                min_score = required_contents.get(section.location.to_deprecated_string())
                if min_score is not None:
                    row_sequential.append('{}'.format('passed' if percentage >= min_score else 'failed'))
                    row_sequential.append('{}% (min score {}%)'.format(percentage, min_score))
                else:
                    row_sequential.append('')
                    row_sequential.append('{}%'.format(percentage))

                row_vertical = []
                for problem, score in section.problem_scores.items():
                    possible = float(score.possible)
                    earned = float(score.earned)
                    problem_name = modulestore().get_item(problem).display_name

                    student_module = StudentModule.objects.filter(
                        module_state_key=problem,
                        student_id=user.id
                    ).first()
                    if student_module and possible:
                        state = json.loads(student_module.state)
                        row_xblock = [
                            '',
                            problem_name,
                            student_module.modified,
                            state.get('attempts', 1),
                            '{}'.format('passed' if possible == earned else 'failed'),
                            '{0:.0%}'.format(earned/possible)
                        ]
                    else:
                        row_xblock = [
                            '',
                            problem_name,
                            '',
                            0,
                            '',
                            '0%'
                        ]
                    row_vertical.append(row_xblock)

                csv_rows.append(row_sequential)
                csv_rows += row_vertical

    return header, csv_rows
