from django.apps import apps
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.hera.mongo import BLOCK_ID, USER, c_user_lesson_coins
from xmodule.modulestore.django import modulestore


def get_medal(points):
    if 90 <= points <= 100:
        return "platinum"
    elif 80 <= points <= 89:
        return "gold"
    elif 70 <= points <= 79:
        return "silver"
    elif 60 <= points <= 69:
        return "copper"


def get_lesson_summary_xblock_context(user, course_key, current_unit):
    """
    Get lesson_summary xblock final grades.
    """
    course_grade = CourseGradeFactory().read(user, course_key=course_key)
    courseware_summary = course_grade.chapter_grades.values()

    points = 0
    lesson_title = ''

    for subsection in modulestore().get_items(course_key):
        for unit in subsection.get_children():
            if unit.location.block_id == current_unit:
                lesson_title = subsection.display_name
                current_subsection = subsection
                break

    for chapter in courseware_summary:
        if not chapter['display_name'] == "hidden":
            for subsection in chapter['sections']:  # the sections in chapter are actually subsection
                if subsection.location.block_id == current_subsection.location.block_id:
                    try:
                        points = int(subsection.all_total.earned / subsection.all_total.possible * 100)
                    except ZeroDivisionError:
                        points = 0
                    break

    return {'lesson_title': lesson_title, 'points': points, 'medal': get_medal(points)}



def recalculate_coints(course_id, block_id, user_id, cost=0):
    course = modulestore().get_course(CourseKey.from_string(course_id))
    subsection_id = None
    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for block in unit.get_children():
                    if block.scope_ids.usage_id.block_id == block_id:
                        subsection_id = subsection.scope_ids.usage_id.block_id
                        break

    user_lesson_coins = c_user_lesson_coins().find_one({
        BLOCK_ID: subsection_id,
        USER: user_id,
    })
    if user_lesson_coins and cost <= user_lesson_coins.get('coins'):
        coins_balance = user_lesson_coins.get('coins') - cost
        c_user_lesson_coins().update(
            {
                BLOCK_ID: subsection_id,
                USER: user_id,
            },
            {
                '$set': {
                    'coins': coins_balance,
                }
            },
            upsert=True
        )
        return coins_balance
    return None


def get_scaffold():
    Scaffold = apps.get_model('hera', 'Scaffold')
    return Scaffold.get_scaffold()
