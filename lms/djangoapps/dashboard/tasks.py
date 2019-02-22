"""
This file contains celery tasks sysdashboard
"""
import logging
import time
import StringIO

import xlwt
from celery import task
from django.core.cache import cache
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from student.roles import CourseStaffRole, CourseInstructorRole
from xmodule.modulestore.django import modulestore

from .models import EmailsAddressMailing


@task(name='mass_sending_report')
def mass_sending_report():
    connection = get_connection()
    xls_file = get_courses_xls()
    email_list = []
    for email in EmailsAddressMailing.objects.filter(active=True):
        email_message = EmailMessage('Catalogue Email Service', 'Hi all,\nThe list of courses is in the attachment.', settings.EMAIL_FROM, [email.email],)
        email_message.attach('Courses_report.xls', xls_file.getvalue(), 'application/vnd.ms-excel')
        email_list.append(email_message)
    connection.send_messages(tuple(email_list))
    
@task()
def send_report_email(request, email_address):
    xls_file = get_courses_xls()
    email_message = EmailMessage('Catalogue Email Service', 'Hi all,\nThe list of courses is in the attachment.', settings.EMAIL_FROM, [email_address],)
    email_message.attach('Courses_{0}.xls'.format(request.META['SERVER_NAME']), xls_file.getvalue(), 'application/vnd.ms-excel')
    email_message.send()

def get_courses_xls():
    """
    Getting course data and return xls file
    _____________________________________________________________________________________
    | Course URL | Course Run ID  | Course name | Enrollment end date | Course end date |
    """
    data = []
    module_store = modulestore()
    for course in module_store.get_courses():
        enroll_end_date = course.enrollment_end.strftime("%m/%d/%Y") if course.enrollment_end else ''
        end_date = course.end.strftime("%m/%d/%Y") if course.end else ''
        course_url = '{}{}'.format(
            settings.LMS_ROOT_URL,
            reverse('course_root', kwargs={'course_id': course.id})
        )
        datum = [course_url, course.id.run, course.display_name,
                enroll_end_date, end_date]
        data.append(datum)

    header = [('Course URL', 16000),
              ('Course Run ID', 5000),
              (_('Course name'), 10000),
              (_('Enrollment end date'), 5000),
              (_('Course end date'), 5000)]
    return return_xls(header, data)

def return_xls(header, data):
    """
    Xls file generation
    """
    xls_file = StringIO.StringIO()
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Courses')

    style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = xlwt.Style.colour_map['gray25']
    style.pattern = pattern

    row_num = 0
    for col_num in range(len(header)):
        ws.write(row_num, col_num, header[col_num][0], style)
        ws.col(col_num).width = header[col_num][1]

    for row in data:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num])

    ws.set_panes_frozen(True)
    ws.set_horz_split_pos(1)
    wb.save(xls_file)
    return xls_file
