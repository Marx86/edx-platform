from django.http import Http404
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    ProgramProgressMeter,
    get_program_marketing_url
)


@require_GET
def program_listing(request, user=None):
    """View a list of programs in which the user is engaged."""
    programs_config = ProgramsApiConfig.current()
    if not programs_config.enabled:
        raise Http404

    meter = ProgramProgressMeter(user)

    context = {
        'disable_courseware_js': True,
        'marketing_url': get_program_marketing_url(programs_config),
        'nav_hidden': True,
        'programs': user and meter.engaged_programs or meter.programs,
        'progress': meter.progress(),
        'show_program_listing': programs_config.enabled,
        'uses_pattern_library': True,
    }

    return render_to_response('learner_dashboard/programs.html', context)

