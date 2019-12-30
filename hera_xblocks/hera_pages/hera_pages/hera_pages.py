"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import JSONField
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xblockutils.resources import ResourceLoader

loader = ResourceLoader(__name__)
class HeraPagesXBlock(StudioEditableXBlockMixin, XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.

    # TO-DO: delete count, and define your own fields.
    editable_fields = ('data',)
    data = JSONField()

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
        return self.data.get("sliderBar")

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")
    
    @XBlock.json_handler
    def get_data(self, somedata, sufix=''):
        return self.data

    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        """
        The primary view of the HeraPagesXBlock, shown to students
        when viewing courses.
        """
        
        html = loader.render_django_template(
            'static/html/hera_pages.html',
            context={"data": self.data}
        )
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/hera_pages.css"))
        frag.add_javascript(self.resource_string("static/js/src/hera_pages.js"))

        # slick jquery cdn
        frag.add_css_url("https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.8.1/slick.css")
        frag.add_css_url("https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.8.1/slick-theme.css")
        
        frag.add_javascript_url("https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.8.1/slick.js")
        
        frag.add_javascript_url("https://cdn.jsdelivr.net/gh/vast-engineering/jquery-popup-overlay@2/jquery.popupoverlay.min.js")
      
        frag.initialize_js('HeraPagesXBlock')
        return frag
