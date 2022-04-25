"""
This module contains various configuration settings via
waffle switches for the instructor_task app.
"""

from edx_toggles.toggles import LegacyWaffleSwitchNamespace

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'instructor_task'

# TODO: Remove and replace with direct references to each switch.
WAFFLE_SWITCHES = LegacyWaffleSwitchNamespace(name=WAFFLE_NAMESPACE)

# Waffle switches
# TODO: Replace with WaffleSwitch(). See WAFFLE_SWITCHES comment.
OPTIMIZE_GET_LEARNERS_FOR_COURSE = 'optimize_get_learners_for_course'

# Course override flags
GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY = CourseWaffleFlag(
    f'{WAFFLE_NAMESPACE}.generate_problem_grade_report_verified_only', __name__
)

GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY = CourseWaffleFlag(
    f'{WAFFLE_NAMESPACE}.generate_course_grade_report_verified_only', __name__
)


def optimize_get_learners_switch_enabled():
    """
    Returns True if optimize get learner switch is enabled, otherwise False.
    """
    return WAFFLE_SWITCHES.is_enabled(OPTIMIZE_GET_LEARNERS_FOR_COURSE)


def problem_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return GENERATE_PROBLEM_GRADE_REPORT_VERIFIED_ONLY.is_enabled(course_id)


def course_grade_report_verified_only(course_id):
    """
    Returns True if problem grade reports should only
    return rows for verified students in the given course,
    False otherwise.
    """
    return GENERATE_COURSE_GRADE_REPORT_VERIFIED_ONLY.is_enabled(course_id)
