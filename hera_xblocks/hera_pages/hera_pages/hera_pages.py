"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import JSONField, Scope, String, Boolean
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xblockutils.resources import ResourceLoader

loader = ResourceLoader(__name__)


class HeraPagesXBlock(StudioEditableXBlockMixin, XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    editable_fields = ('data',)

    display_name = String(default="Hera Pages")
    data = JSONField()
    user_answers = JSONField(scope=Scope.user_state, default='')
    viewed = Boolean(scope=Scope.user_state, default=False)

    @property
    def img_url(self):
        """return images for the pages"""
        return self.data.get("imgUrl")

    @property
    def frame_url(self):
        """return iframe for the pages"""
        return self.data.get("iframeUrl")

    @property
    def slider_bar(self):
        """return html content for the slide bar in pages"""
        return self.data.get("sliderBar", [])

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def get_context(self):
        return {
            "data": self.data,
            "user_answers": self.user_answers,
            "block_id": self.location.block_id,
            "viewed": self.viewed
        }
    
    def get_content_html(self):
        html = loader.render_mako_template(
            'static/html/hera_pages.html',
            context=self.get_context()
        )
        return html
    
    @XBlock.json_handler
    def render_correct_filled_tables(self, data, suffix=''):
        tables_html = []
        for slider_item in self.slider_bar:
            if slider_item.get('tableData'):
                table_html = loader.render_mako_template(
                    'static/html/correct_filled_table.html',
                    context={'data': slider_item.get('tableData')}
                )
                tables_html.append(table_html)
        return {'tables_html': tables_html}

    @XBlock.json_handler
    def all_slides_viewed(self, data, sufix=''):
        self.viewed = True
        return True

    @XBlock.json_handler
    def render_html(self, data, sufix=''):
        return {
            'content': self.get_content_html()
        }

    @XBlock.json_handler
    def get_data(self, somedata, sufix=''):
        return self.data

    def student_view(self, context=None):
        """
        The primary view of the HeraPagesXBlock, shown to students
        when viewing courses.
        """
        
        html = loader.render_mako_template(
            'static/html/main.html',
            context={'block_id': self.location.block_id}
        )
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/hera_pages.css"))
        frag.add_javascript(self.resource_string("static/js/src/hera_pages.js"))
      
        frag.initialize_js('HeraPagesXBlock', json_args=self.get_context())
        return frag

    @XBlock.json_handler
    def submit(self, data, suffix=''):
        self.user_answers = data.get("answers")
        return True
