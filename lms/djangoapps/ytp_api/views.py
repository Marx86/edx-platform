"""
APIView endpoints for creating user
"""
import logging
from uuid import uuid4
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from openedx.core.djangoapps.user_api.accounts.api import check_account_exists
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from student.views import create_account_with_params

log = logging.getLogger(__name__)


class CreateUserAccountWithoutPasswordView(APIView):
    """
    Create user account without password.
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (ApiKeyHeaderPermission,)
    
    _error_dict = {
        "username": "Username is required parameter.",
        "email": "Email is required parameter.",
        "gender": "Gender parameter must contain 'm'(Male), 'f'(Female) or 'o'(Other. Default if parameter is missing)"
    }
    
    def post(self, request):
        """
        Create a user by email, login
        """
        data = request.data
        data['honor_code'] = "True"
        data['terms_of_service'] = "True"
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        try:
            email = self._check_available_required_params(request.data.get('email'), "email")
            username = self._check_available_required_params(request.data.get('username'), "username")
            data['gender'] = self._check_available_required_params(
                request.data.get('gender', 'o'), "gender", ['m', 'f', 'o']
            )
            if check_account_exists(username=username, email=email):
                return Response(data={"error_message": "User already exists"}, status=status.HTTP_409_CONFLICT)
            data['name'] = "{} {}".format(first_name, last_name).strip() if first_name or last_name else username
            data['password'] = uuid4().hex
            user = create_account_with_params(request, data)
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.save()
        except ValueError as e:
            log.error(e.message)
            return Response(
                data={"error_message": e.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValidationError as e:
            return Response(data={"error_message": e.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={'user_id': user.id, 'username': username}, status=status.HTTP_200_OK)


    def _check_available_required_params(self, parameter, parameter_name, values_list=None):
        """
        Raise ValueError if param not available or not in list. Also return param.
    
        :param parameter: object
        :param parameter_name: string. Parameter's name
        :param values_list: List of values
    
        :return: parameter
        """
        if not parameter or (values_list and isinstance(values_list, list) and parameter not in values_list):
            raise ValueError(self._error_dict[parameter_name].format(value=parameter))
        return parameter
