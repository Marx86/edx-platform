from edxmako.shortcuts import render_to_response


class HttpExcetionRender:
    def process_exception(self, request, exception):
        if isinstance(exception, Exception):
            name = exception.__class__.__name__
            if not name.startswith('Http'):
                return
            name = name.replace('Http', '')
            try:
                error_response = render_to_response('static_templates/{}.html'.format(name))
                return error_response
            except:
                pass
