"""
This module creates a sysadmin dashboard for managing and viewing
courses.
"""
import unicodecsv as csv
import json
import logging
import os
import StringIO
import subprocess

import mongoengine
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import condition
from django.views.generic.base import TemplateView
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from path import Path as path

import dashboard.git_import as git_import
import track.views
from courseware.courses import get_course_by_id
from dashboard.git_import import GitImportError
from dashboard.models import CourseImportLog
from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from openedx.core.djangoapps.external_auth.views import generate_password
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from ccx.utils import get_course_chapters
from student.views import get_course_enrollments
from student.models import CourseEnrollment, Registration, UserProfile
from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore.django import modulestore
from search.search_engine_base import SearchEngine
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from courseware import models

log = logging.getLogger(__name__)


class SysadminDashboardView(TemplateView):
    """Base class for sysadmin dashboard views with common methods"""

    template_name = 'sysadmin_dashboard.html'

    def __init__(self, **kwargs):
        """
        Initialize base sysadmin dashboard class with modulestore,
        modulestore_type and return msg
        """

        self.def_ms = modulestore()
        self.msg = u''
        self.datatable = []
        super(SysadminDashboardView, self).__init__(**kwargs)

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(login_required)
    @method_decorator(cache_control(no_cache=True, no_store=True,
                                    must_revalidate=True))
    @method_decorator(condition(etag_func=None))
    def dispatch(self, *args, **kwargs):
        return super(SysadminDashboardView, self).dispatch(*args, **kwargs)

    def get_courses(self):
        """ Get an iterable list of courses."""

        return self.def_ms.get_courses()

    def return_csv(self, filename, header, data):
        """
        Convenient function for handling the http response of a csv.
        data should be iterable and is used to stream object over http
        """

        csv_file = StringIO.StringIO()
        writer = csv.writer(csv_file, dialect='excel', quotechar='"',
                            quoting=csv.QUOTE_ALL)

        writer.writerow(header)

        # Setup streaming of the data
        def read_and_flush():
            """Read and clear buffer for optimization"""
            csv_file.seek(0)
            csv_data = csv_file.read()
            csv_file.seek(0)
            csv_file.truncate()
            return csv_data

        def csv_data():
            """Generator for handling potentially large CSVs"""
            for row in data:
                writer.writerow(row)
            csv_data = read_and_flush()
            yield csv_data
        response = HttpResponse(csv_data(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            filename)
        return response


class Users(SysadminDashboardView):
    """
    The status view provides Web based user management, a listing of
    courses loaded, and user statistics
    """

    def fix_external_auth_map_passwords(self):
        """
        This corrects any passwords that have drifted from eamap to
        internal django auth.  Needs to be removed when fixed in external_auth
        """

        msg = ''
        for eamap in ExternalAuthMap.objects.all():
            euser = eamap.user
            epass = eamap.internal_password
            if euser is None:
                continue
            try:
                testuser = authenticate(username=euser.username, password=epass)
            except (TypeError, PermissionDenied, AttributeError), err:
                # Translators: This message means that the user could not be authenticated (that is, we could
                # not log them in for some reason - maybe they don't have permission, or their password was wrong)
                msg += _('Failed in authenticating {username}, error {error}\n').format(
                    username=euser,
                    error=err
                )
                continue
            if testuser is None:
                # Translators: This message means that the user could not be authenticated (that is, we could
                # not log them in for some reason - maybe they don't have permission, or their password was wrong)
                msg += _('Failed in authenticating {username}\n').format(username=euser)
                # Translators: this means that the password has been corrected (sometimes the database needs to be resynchronized)
                # Translate this as meaning "the password was fixed" or "the password was corrected".
                msg += _('fixed password')
                euser.set_password(epass)
                euser.save()
                continue
        if not msg:
            # Translators: this means everything happened successfully, yay!
            msg = _('All ok!')
        return msg

    def create_user(self, uname, name, password=None):
        """ Creates a user (both SSL and regular)"""

        if not uname:
            return _('Must provide username')
        if not name:
            return _('Must provide full name')

        email_domain = getattr(settings, 'SSL_AUTH_EMAIL_DOMAIN', 'MIT.EDU')

        msg = u''
        if settings.FEATURES['AUTH_USE_CERTIFICATES']:
            if '@' not in uname:
                email = '{0}@{1}'.format(uname, email_domain)
            else:
                email = uname
            if not email.endswith('@{0}'.format(email_domain)):
                # Translators: Domain is an email domain, such as "@gmail.com"
                msg += _('Email address must end in {domain}').format(domain="@{0}".format(email_domain))
                return msg
            mit_domain = 'ssl:MIT'
            if ExternalAuthMap.objects.filter(external_id=email,
                                              external_domain=mit_domain):
                msg += _('Failed - email {email_addr} already exists as {external_id}').format(
                    email_addr=email,
                    external_id="external_id"
                )
                return msg
            new_password = generate_password()
        else:
            if not password:
                return _('Password must be supplied if not using certificates')

            email = uname

            if '@' not in email:
                msg += _('email address required (not username)')
                return msg
            new_password = password

        if User.objects.filter(username=uname).exists():
            return _('This username already taken')

        if User.objects.filter(email=email).exists():
            return _('This email already taken')

        user = User(username=uname, email=email, is_active=True)
        user.set_password(new_password)
        try:
            user.save()
        except IntegrityError:
            msg += _('Oops, failed to create user {user}, {error}').format(
                user=user,
                error="IntegrityError"
            )
            return msg

        reg = Registration()
        reg.register(user)

        profile = UserProfile(user=user)
        profile.name = name
        profile.save()

        if settings.FEATURES['AUTH_USE_CERTIFICATES']:
            credential_string = getattr(settings, 'SSL_AUTH_DN_FORMAT_STRING',
                                        '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}')
            credentials = credential_string.format(name, email)
            eamap = ExternalAuthMap(
                external_id=email,
                external_email=email,
                external_domain=mit_domain,
                external_name=name,
                internal_password=new_password,
                external_credentials=json.dumps(credentials),
            )
            eamap.user = user
            eamap.dtsignup = timezone.now()
            eamap.save()

        msg += _('User {user} created successfully!').format(user=user)
        return msg

    def delete_user(self, uname):
        """Deletes a user from django auth"""

        if not uname:
            return _('Must provide username')
        if '@' in uname:
            try:
                user = User.objects.get(email=uname)
            except User.DoesNotExist, err:
                msg = _('Cannot find user with email address {email_addr}').format(email_addr=uname)
                return msg
        else:
            try:
                user = User.objects.get(username=uname)
            except User.DoesNotExist, err:
                msg = _('Cannot find user with username {username} - {error}').format(
                    username=uname,
                    error=str(err)
                )
                return msg
        user.delete()
        return _('Deleted user {username}').format(username=uname)

    def make_common_context(self):
        """Returns the datatable used for this view"""

        self.datatable = {}

        self.datatable = dict(header=[_('Statistic'), _('Value')],
                              title=_('Site statistics'))
        self.datatable['data'] = [[_('Total number of users'),
                                   User.objects.all().count()]]

        self.msg += u'<h2>{0}</h2>'.format(
            _('Courses loaded in the modulestore')
        )
        self.msg += u'<ol>'
        for course in self.get_courses():
            self.msg += u'<li>{0} ({1})</li>'.format(
                escape(course.id.to_deprecated_string()), course.location.to_deprecated_string())
        self.msg += u'</ol>'

    def get(self, request):

        if not request.user.is_staff:
            raise Http404
        self.make_common_context()

        context = {
            'datatable': self.datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'users': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle various actions available on page"""

        if not request.user.is_staff:
            raise Http404

        self.make_common_context()

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {}, page='user_sysdashboard')

        if action == 'download_users':
            header = [_('username'), _('email'), ]
            data = ([u.name, u.user.email] for u in
                    (UserProfile.objects.all().iterator()))
            return self.return_csv('users_{0}.csv'.format(
                request.META['SERVER_NAME']), header, data)
        elif action == 'repair_eamap':
            self.msg = u'<h4>{0}</h4><pre>{1}</pre>{2}'.format(
                _('Repair Results'),
                self.fix_external_auth_map_passwords(),
                self.msg)
            self.datatable = {}
        elif action == 'create_user':
            uname = request.POST.get('student_uname', '').strip()
            name = request.POST.get('student_fullname', '').strip()
            password = request.POST.get('student_password', '').strip()
            self.msg = u'<h4>{0}</h4><p>{1}</p><hr />{2}'.format(
                _('Create User Results'),
                self.create_user(uname, name, password), self.msg)
        elif action == 'del_user':
            uname = request.POST.get('student_uname', '').strip()
            self.msg = u'<h4>{0}</h4><p>{1}</p><hr />{2}'.format(
                _('Delete User Results'), self.delete_user(uname), self.msg)

        context = {
            'datatable': self.datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'users': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)


class Courses(SysadminDashboardView):
    """
    This manages adding/updating courses from git, deleting courses, and
    provides course listing information.
    """
    _searcher = SearchEngine.get_search_engine(getattr(settings, "COURSEWARE_INDEX_NAME", "courseware_index"))

    def git_info_for_course(self, cdir):
        """This pulls out some git info like the last commit"""

        cmd = ''
        gdir = settings.DATA_DIR / cdir
        info = ['', '', '']

        # Try the data dir, then try to find it in the git import dir
        if not gdir.exists():
            git_repo_dir = getattr(settings, 'GIT_REPO_DIR', git_import.DEFAULT_GIT_REPO_DIR)
            gdir = path(git_repo_dir) / cdir
            if not gdir.exists():
                return info

        cmd = ['git', 'log', '-1',
               '--format=format:{ "commit": "%H", "author": "%an %ae", "date": "%ad"}', ]
        try:
            output_json = json.loads(subprocess.check_output(cmd, cwd=gdir))
            info = [output_json['commit'],
                    output_json['date'],
                    output_json['author'], ]
        except (ValueError, subprocess.CalledProcessError):
            pass

        return info

    def get_course_from_git(self, gitloc, branch):
        """This downloads and runs the checks for importing a course in git"""

        if not (gitloc.endswith('.git') or gitloc.startswith('http:') or
                gitloc.startswith('https:') or gitloc.startswith('git:')):
            return _("The git repo location should end with '.git', "
                     "and be a valid url")

        return self.import_mongo_course(gitloc, branch)

    def import_mongo_course(self, gitloc, branch):
        """
        Imports course using management command and captures logging output
        at debug level for display in template
        """

        msg = u''

        log.debug('Adding course using git repo %s', gitloc)

        # Grab logging output for debugging imports
        output = StringIO.StringIO()
        import_log_handler = logging.StreamHandler(output)
        import_log_handler.setLevel(logging.DEBUG)

        logger_names = ['xmodule.modulestore.xml_importer',
                        'dashboard.git_import',
                        'xmodule.modulestore.xml',
                        'xmodule.seq_module', ]
        loggers = []

        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(import_log_handler)
            loggers.append(logger)

        error_msg = ''
        try:
            git_import.add_repo(gitloc, None, branch)
        except GitImportError as ex:
            error_msg = str(ex)
        ret = output.getvalue()

        # Remove handler hijacks
        for logger in loggers:
            logger.setLevel(logging.NOTSET)
            logger.removeHandler(import_log_handler)

        if error_msg:
            msg_header = error_msg
            color = 'red'
        else:
            msg_header = _('Added Course')
            color = 'blue'

        msg = u"<h4 style='color:{0}'>{1}</h4>".format(color, msg_header)
        msg += u"<pre>{0}</pre>".format(escape(ret))
        return msg

    def make_datatable(self):
        """Creates course information datatable"""

        data = []

        for course in self.get_courses():
            gdir = course.id.course
            data.append([course.display_name, course.id.to_deprecated_string()]
                        + self.git_info_for_course(gdir))

        return dict(header=[_('Course Name'),
                            _('Directory/ID'),
                            # Translators: "Git Commit" is a computer command; see http://gitref.org/basic/#commit
                            _('Git Commit'),
                            _('Last Change'),
                            _('Last Editor')],
                    title=_('Information about all courses'),
                    data=data)

    def get(self, request):
        """Displays forms and course information"""

        if not request.user.is_staff:
            raise Http404

        context = {
            'datatable': self.make_datatable(),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'courses': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle all actions from courses view"""

        if not request.user.is_staff:
            raise Http404

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {},
                                 page='courses_sysdashboard')

        courses = {course.id: course for course in self.get_courses()}
        if action == 'add_course':
            gitloc = request.POST.get('repo_location', '').strip().replace(' ', '').replace(';', '')
            branch = request.POST.get('repo_branch', '').strip().replace(' ', '').replace(';', '')
            self.msg += self.get_course_from_git(gitloc, branch)

        elif action == 'download_course_users':
            course_id = request.POST.get('course_id', '').strip()
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
            course_found = False
            if course_key in courses:
                course_found = True
                course = courses[course_key]
            else:
                try:
                    course = get_course_by_id(course_key)
                    course_found = True
                except Exception, err:   # pylint: disable=broad-except
                    self.msg += _(
                        'Error - cannot get course with ID {0}<br/><pre>{1}</pre>'
                    ).format(
                        course_key,
                        escape(str(err))
                    )
            if course_found:
                # donload csv list of cource students
                data = []
                # Remove current site orgs from the "filter out" list, if applicable.
                # We want to filter and only show enrollments for courses within
                # the organizations defined in configuration for the current site.
                org_filter_out_set = configuration_helpers.get_all_orgs()
                course_org_filter = configuration_helpers.get_current_site_orgs()
                if course_org_filter:
                    org_filter_out_set = org_filter_out_set - set(course_org_filter)

                enrolled_students = User.objects.filter(
                    courseenrollment__course_id=course_key)

                # returns a list of chapters ids
                # for parsing children (sequentials) in course tree
                course_chapters = get_course_chapters(course_key)

                course_obj = CourseStructure.objects.get(course_id=course_key)  # course content tree, serialised

                # deserialising and converting to OrderedDict with the blocks in the order that they appear in the
                # course
                course_ordered = course_obj.ordered_blocks  # OrderedDict

                def get_children(parent):
                    """
                    Getting children method
                    """
                    children = course_ordered[parent].get('children', [])
                    return children

                # getting list of all sequentials (child for chapter)
                sequentials = []  # The subsections defined in the course outline
                for chapter in course_chapters:
                    one_chapter_seqs = get_children(chapter)
                    for seq in one_chapter_seqs:
                        sequentials.append(seq)

                # getting list of all verticals (child for sequential)
                verticals = []  # The units defined in the course outline
                for sequential in sequentials:
                    one_seq_verts = get_children(sequential)
                    for vert in one_seq_verts:
                        verticals.append(vert)

                # getting vertical (unit) names
                unit_names = []
                for vertical in verticals:
                    unit_name = course_ordered[vertical].get('display_name')
                    unit_names.append(unit_name)

                header = [_('username'), _('email'), _('registration date'), _('enrolled courses'), ('last login'), 'last visit', ]
                for name in unit_names:
                    header.append(name)  # adding unit names to the table header

                for u in enrolled_students:  # u - User object, enrolled to current course
                    db_query = models.StudentModule.objects.filter(
                        course_id__exact=course_key,
                        student_id=u.id
                    )   # querySet StudentModule
                    last_visit_id = db_query.all().order_by('-modified').values_list('module_state_key', flat=True)[:1]
                    try:
                        last_visit = course_ordered[last_visit_id[0]].get('display_name')
                    except Exception:
                        last_visit = 'New to course'

                    visited_in_course = []
                    for block in db_query.all().values('module_state_key'):
                        msk = block['module_state_key']
                        visited_in_course.append(msk)  # usageKeys for course parts where student have been

                    # getting other student enrollments
                    enrollments = list(get_course_enrollments(u, course_org_filter, org_filter_out_set))
                    enrolled_ids = ', '.join([enrollment.course_id.course for enrollment in enrollments])

                    # comparing course structure chunks (problem, video, html) with units visited in course
                    seq_positions = {}  # getting positions for sequential module_types
                    visited_in_seq = db_query.filter(module_type='sequential')
                    for v in visited_in_seq.values('module_state_key', 'state'):
                        # structure example: v = {
                        # 'module_state_key': u'block-v1:edX+DemoX+Demo_Course+type@sequential+block@edx_introduction', # 'state': u'{"position": 1}'
                        # }
                        key = v['module_state_key']
                        val = json.loads(v['state']).get('position')
                        seq_positions[key] = val
                    status_list = []
                    for sequential in sequentials:
                        for vertical in get_children(sequential):
                            for unit in get_children(vertical):
                                if course_ordered[unit]['block_type'] in ['video', 'problem']:
                                    if unit in visited_in_course:
                                        status = '+'
                                        break   # if we have visit in any of vertical children - it marks '+'
                                # scipping discussion units
                                elif course_ordered[unit]['block_type'] in ['discussion']:
                                    continue
                                # for html-only pages:
                                else:
                                    current_seq_children_list = get_children(sequential)
                                    vert_position_in_seq = current_seq_children_list.index(vertical)
                                    try:
                                        last_visit_in_seq_position = seq_positions[sequential]
                                        if (vert_position_in_seq < last_visit_in_seq_position):
                                            status = '+'
                                            break
                                        else:
                                            status = '-'
                                    except Exception:
                                        status = '-'
                            status_list.append(status)
                    # some default users could be without last_login, so:
                    try:
                        last_login = u.last_login.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        last_login = '-'
                    d = [
                        u.profile.name,
                        u.email,
                        u.date_joined.strftime('%Y-%m-%d %H:%M'),
                        enrolled_ids,
                        last_login,
                        last_visit,
                    ] + status_list
                    data.append(d)
                return self.return_csv(
                    'users_{0}_{1}.csv'.format(request.META['SERVER_NAME'], course_id), header, data
                )

        elif action == 'del_course':
            course_id = request.POST.get('course_id', '').strip()
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
            course_found = False
            if course_key in courses:
                course_found = True
                course = courses[course_key]
            else:
                try:
                    course = get_course_by_id(course_key)
                    course_found = True
                except Exception, err:   # pylint: disable=broad-except
                    self.msg += _(
                        'Error - cannot get course with ID {0}<br/><pre>{1}</pre>'
                    ).format(
                        course_key,
                        escape(str(err))
                    )

            if course_found:
                # delete course that is stored with mongodb backend
                self.def_ms.delete_course(course.id, request.user.id)

                # delete search index
                try:
                    response = self._searcher.search(doc_type="courseware_content", field_dictionary={'course': course_id})
                    result_ids = [result["data"]["id"] for result in response["results"]]
                    self._searcher.remove('courseware_content', result_ids)
                    self._searcher.remove('course_info', [course_id])
                except Exception as e:  # pragma: no cover
                    log.error(e.message)

                CourseOverview.objects.filter(id=course.id).delete()

                # don't delete user permission groups, though
                self.msg += \
                    u"<font color='red'>{0} {1} = {2} ({3})</font>".format(
                        _('Deleted'), course.location.to_deprecated_string(), course.id.to_deprecated_string(), course.display_name)

        context = {
            'datatable': self.make_datatable(),
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'courses': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)


class Staffing(SysadminDashboardView):
    """
    The status view provides a view of staffing and enrollment in
    courses that include an option to download the data as a csv.
    """

    def get(self, request):
        """Displays course Enrollment and staffing course statistics"""

        if not request.user.is_staff:
            raise Http404
        data = []

        for course in self.get_courses():
            datum = [course.display_name, course.id]
            datum += [CourseEnrollment.objects.filter(
                course_id=course.id).count()]
            datum += [CourseStaffRole(course.id).users_with_role().count()]
            datum += [','.join([x.username for x in CourseInstructorRole(
                course.id).users_with_role()])]
            data.append(datum)

        datatable = dict(header=[_('Course Name'), _('course_id'),
                                 _('# enrolled'), _('# staff'),
                                 _('instructors')],
                         title=_('Enrollment information for all courses'),
                         data=data)
        context = {
            'datatable': datatable,
            'msg': self.msg,
            'djangopid': os.getpid(),
            'modeflag': {'staffing': 'active-section'},
            'edx_platform_version': getattr(settings, 'EDX_PLATFORM_VERSION_STRING', ''),
        }
        return render_to_response(self.template_name, context)

    def post(self, request):
        """Handle all actions from staffing and enrollment view"""

        action = request.POST.get('action', '')
        track.views.server_track(request, action, {},
                                 page='staffing_sysdashboard')

        if action == 'get_staff_csv':
            data = []
            roles = [CourseInstructorRole, CourseStaffRole, ]

            for course in self.get_courses():
                for role in roles:
                    for user in role(course.id).users_with_role():
                        datum = [course.id, role, user.username, user.email,
                                 user.profile.name]
                        data.append(datum)
            header = [_('course_id'),
                      _('role'), _('username'),
                      _('email'), _('full_name'), ]
            return self.return_csv('staff_{0}.csv'.format(
                request.META['SERVER_NAME']), header, data)

        return self.get(request)


class GitLogs(TemplateView):
    """
    This provides a view into the import of courses from git repositories.
    It is convenient for allowing course teams to see what may be wrong with
    their xml
    """

    template_name = 'sysadmin_dashboard_gitlogs.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Shows logs of imports that happened as a result of a git import"""

        course_id = kwargs.get('course_id')
        if course_id:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        page_size = 10

        # Set mongodb defaults even if it isn't defined in settings
        mongo_db = {
            'host': 'localhost',
            'user': '',
            'password': '',
            'db': 'xlog',
        }

        # Allow overrides
        if hasattr(settings, 'MONGODB_LOG'):
            for config_item in ['host', 'user', 'password', 'db', ]:
                mongo_db[config_item] = settings.MONGODB_LOG.get(
                    config_item, mongo_db[config_item])

        mongouri = 'mongodb://{user}:{password}@{host}/{db}'.format(**mongo_db)

        error_msg = ''

        try:
            if mongo_db['user'] and mongo_db['password']:
                mdb = mongoengine.connect(mongo_db['db'], host=mongouri)
            else:
                mdb = mongoengine.connect(mongo_db['db'], host=mongo_db['host'])
        except mongoengine.connection.ConnectionError:
            log.exception('Unable to connect to mongodb to save log, '
                          'please check MONGODB_LOG settings.')

        if course_id is None:
            # Require staff if not going to specific course
            if not request.user.is_staff:
                raise Http404
            cilset = CourseImportLog.objects.order_by('-created')
        else:
            try:
                course = get_course_by_id(course_id)
            except Exception:
                log.info('Cannot find course %s', course_id)
                raise Http404

            # Allow only course team, instructors, and staff
            if not (request.user.is_staff or
                    CourseInstructorRole(course.id).has_user(request.user) or
                    CourseStaffRole(course.id).has_user(request.user)):
                raise Http404
            log.debug('course_id=%s', course_id)
            cilset = CourseImportLog.objects.filter(
                course_id=course_id
            ).order_by('-created')
            log.debug('cilset length=%s', len(cilset))

        # Paginate the query set
        paginator = Paginator(cilset, page_size)
        try:
            logs = paginator.page(request.GET.get('page'))
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            # If the page is too high or low
            given_page = int(request.GET.get('page'))
            page = min(max(1, given_page), paginator.num_pages)
            logs = paginator.page(page)

        mdb.disconnect()
        context = {
            'logs': logs,
            'course_id': course_id.to_deprecated_string() if course_id else None,
            'error_msg': error_msg,
            'page_size': page_size
        }

        return render_to_response(self.template_name, context)
