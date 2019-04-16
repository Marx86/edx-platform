"""
Edeos views.

e.g. wallets management.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from edeos.edeos_keys import EDEOS_API_KEY, EDEOS_API_SECRET
from edeos.utils import send_edeos_api_request, get_user_id


@login_required
@csrf_exempt
def update_wallet(request):
    if request.method == 'POST' and request.is_ajax():
        data = request.POST.copy()
        if data.get('wallet_name'):
            edeos_post_data = {
                'payload': {
                    'student_id': get_user_id(request.user),
                    'client_id': EDEOS_API_KEY,
                    'wallet': data.get('wallet_name')
                },
                "api_endpoint": "wallet_update",
                "key": EDEOS_API_KEY,  # settings.EDEOS_API_KEY,  # TODO revert to settings
                "secret": EDEOS_API_SECRET,  # settings.EDEOS_API_SECRET,  # TODO revert to settings
                "base_url": "http://195.160.222.156/api/point/v1/"
            }
            response = send_edeos_api_request(**edeos_post_data)
            return HttpResponse(response, content_type="application/json")
        return HttpResponse(status=400)
    else:
        return HttpResponse(status=405)


@login_required
@csrf_exempt
def generate_wallet(request):
    if request.method == 'POST' and request.is_ajax():
        edeos_post_data = {
            'payload': {
                'student_id': get_user_id(request.user),
                'client_id': EDEOS_API_KEY,
            },
            "api_endpoint": "wallet_store",
            "key": EDEOS_API_KEY,  # settings.EDEOS_API_KEY,  # TODO revert to settings
            "secret": EDEOS_API_SECRET,  # settings.EDEOS_API_SECRET,  # TODO revert to settings
            "base_url": "http://195.160.222.156/api/point/v1/"
        }
        response = send_edeos_api_request(**edeos_post_data)
        return HttpResponse(response, content_type="application/json")
    else:
        return HttpResponse(status=405)
