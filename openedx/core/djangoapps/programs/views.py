from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response

from lms.djangoapps.learner_dashboard.programs import ProgramsFragmentView
from openedx.core.djangoapps.programs.models import ProgramsApiConfig


@require_GET
def program_listing(request, user=None):
    """View a list of programs in which the user is engaged."""
    programs_config = ProgramsApiConfig.current()
    programs_fragment = ProgramsFragmentView().render_to_fragment(request, programs_config=programs_config)

    context = {
        'disable_courseware_js': True,
        'programs_fragment': programs_fragment,
        'nav_hidden': True,
        'show_dashboard_tabs': True,
        'show_program_listing': programs_config.enabled,
        'uses_pattern_library': True,
    }

    return render_to_response('learner_dashboard/programs.html', context)
