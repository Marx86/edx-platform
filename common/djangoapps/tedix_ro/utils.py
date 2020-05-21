"""
Helper Methods
"""
import json
from urlparse import urljoin

from babel.dates import format_datetime
from django.apps import apps
from django.conf import settings
from django.urls import reverse

from courseware.models import StudentModule
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from lms.djangoapps.grades.course_data import CourseData
from lms.djangoapps.grades.course_grade import CourseGrade
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_payment_link(user):
    if not user:
        return ''
    return 'http://tedix.kloudstores.com/?email={email}&type=student'.format(
        email=user.email
    )


def report_data_preparation(user, course):
    """
    Takes user and course
    Return "report_data" - data for extended report
    """
    Question = apps.get_model('tedix_ro', 'Question')
    StudentReportSending = apps.get_model('tedix_ro', 'StudentReportSending')
    questions_data = []
    header = []
    video_questions = Question.objects.filter(video_lesson__course=course.id)

    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for problem in unit.get_children():
                    if problem.location.block_type == 'problem':
                        student_module = StudentModule.objects.filter(student=user, module_state_key=problem.location).first()
                        if student_module:
                            attempts = json.loads(student_module.state).get("attempts", 0)
                            correct_map = json.loads(student_module.state).get('correct_map', {})
                            correctness = correct_map.values()[0].get('correctness') if correct_map else False
                            done = True if correctness == 'correct' else False
                        else:
                            attempts = 0
                            done = False
                        header.append(problem.display_name)
                        questions_data.append((problem.display_name, attempts, done))

    questions = video_questions.values('question_id', 'video_lesson__video_id').distinct()
    user_video_questions = video_questions.filter(video_lesson__user=user)

    if user_video_questions:
        for video_question in user_video_questions:
            questions = questions.exclude(video_lesson__video_id=video_question.video_lesson.video_id)
            questions_data.append((video_question.question_id, video_question.attempt_count, True))
            header.append(video_question.question_id)

    for question in questions:
        questions_data.append((question.get('question_id'), 0, False))
        header.append(question.get('question_id'))

    student_report = StudentReportSending.objects.filter(course_id=course.id, user_id=user.id).first()

    report_data = {
        'full_name': user.profile.name or user.username,
        'completion': not bool([item for item in questions_data if item[1] == 0]) and lesson_course_grade(user, course.id).passed,
        'questions': questions_data,
        'percent': "{}%".format(student_report.grade * 100) if student_report else "n/a"
    }
    return header, report_data


def light_report_data_preparation(user, course):
    Question = apps.get_model('tedix_ro', 'Question')
    StudentCourseDueDate = apps.get_model('tedix_ro', 'StudentCourseDueDate')
    count_answer_first_attempt = 0
    completion = True
    count_questions = 0

    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for problem in unit.get_children():
                    if problem.location.block_type == 'problem':
                        student_module = StudentModule.objects.filter(
                            student=user,
                            module_state_key=problem.location
                        ).first()
                        if student_module:
                            attempts = json.loads(student_module.state).get("attempts", 0)
                            if attempts == 1:
                                count_answer_first_attempt += 1
                            if attempts == 0:
                                completion = False
                        else:
                            completion = False
                        count_questions += 1
    count_questions += Question.objects.filter(video_lesson__course=course.id).values('question_id').distinct().count()
    count_answer_first_attempt += Question.objects.filter(video_lesson__course=course.id, video_lesson__user=user, attempt_count=1).count()
    student_course_due_date = StudentCourseDueDate.objects.filter(student__user=user, course_id=course.id).first()
    due_date = student_course_due_date.due_date if student_course_due_date else None
    report_data = {
        'student_name': user.profile.name or user.username,
        'lesson': course.display_name,
        'completion': completion,
        'count_answer_first_attempt': count_answer_first_attempt,
        'count_questions': count_questions,
        'percent': (count_answer_first_attempt * 100 / count_questions) if count_questions else 100,
        'due_date': format_datetime(due_date, "yy.MM.dd hh:mm a", locale='en') if due_date else 'N/A',
        'report_url': urljoin(
            configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL),
            reverse('extended_report', kwargs={'course_key': course.id})
        )
    }
    return report_data


def lesson_course_grade(user, course_key):
    """
    Return "CourseGrade" object for "user" and "course_key"
    """
    if PersistentGradesEnabledFlag.feature_enabled(course_key):
        course_grade = CourseGradeFactory().read(user=user, course_key=course_key)
    else:
        course_data = CourseData(user, course_key=course_key)
        course_grade = CourseGrade(
            user,
            course_data
        )
        course_grade = course_grade.update()
    return course_grade


def all_problems_have_answer(user, course_grade):
    """
    Return "True" if all problems have attempts
    """
    for problem in course_grade.problem_scores:
        student_module = StudentModule.objects.filter(
            student=user,
            module_state_key=problem
        ).first()
        if not student_module or not json.loads(student_module.state).get("attempts"):
            return False
    return True


def video_lesson_complited(user, course_key):
    """
    Return "True" if all question in video lesson has attempts
    """
    Question = apps.get_model('tedix_ro', 'Question')
    video_questions = Question.objects.filter(video_lesson__course=course_key)
    questions_count = video_questions.values('question_id').distinct().count()
    answered_questions_count = video_questions.filter(video_lesson__user=user).exclude(attempt_count=0).count()
    return questions_count == answered_questions_count
