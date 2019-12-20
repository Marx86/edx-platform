"""TO-DO: Write a description of what this XBlock is."""
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import JSONField, Scope, List, Integer
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

loader = ResourceLoader(__name__)


class QuestionXBlock(StudioEditableXBlockMixin, XBlock):
    """
    TO-DO: document what your XBlock does.
    """
    editable_fields = ('data',)
    has_score = True

    data = JSONField(default={})
    user_confidence = Integer(scope=Scope.user_state)
    user_answer = List(scope=Scope.user_state)

    @property
    def img_url(self):
        return self.data.get("imgUrl")

    @property
    def iframe_url(self):
        return self.data.get("iframeUrl")

    @property
    def description(self):
        return self.data.get("description")

    @property
    def question(self):
        return self.data.get("question")

    @property
    def options(self):
        return self.data.get("question", {}).get("options")

    @property
    def answer(self):
        return self.question.get("answer")

    @property
    def preciseness(self):
        preciseness = self.question.get("preciseness")
        preciseness_values = preciseness.split('%')
        try:
            preciseness_value = float(preciseness_values[0]) if preciseness_values else 0
        except ValueError:
            preciseness_value = 0

        if preciseness.rfind('%') > -1:
            return preciseness_value * self.answer / 100
        else:
            return preciseness_value

    @property
    def confidence_text(self):
        return self.data.get("confidenceText")

    @property
    def correct_answer_text(self):
        return self.data.get("correctAnswerText")

    @property
    def incorrect_answer_text(self):
        return self.data.get("incorrectAnswerText")

    @property
    def rephrase(self):
        return self.data.get("rephrase")

    @property
    def break_down(self):
        return self.data.get("breakDown")

    @property
    def teach_me(self):
        return self.data.get("teachMe")

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def get_context(self):
        return {
            "user_answer": self.user_answer,
            "question": self.question,
            "img_url": self.img_url,
            "iframe_url": self.iframe_url,
            "description": self.description,
            "confidence_text": self.confidence_text,
            "correct_answer_text": self.correct_answer_text,
            "incorrect_answer_text": self.incorrect_answer_text,
            "options": self.options,
            "rephrase": self.rephrase,
            "break_down": self.break_down,
            "teach_me": self.teach_me
        }

    def student_view(self, context=None):
        """
        The primary view of the QuestionXBlock, shown to students
        when viewing courses.
        """
        html = loader.render_django_template(
            'static/html/question.html',
            context=self.get_context()
        )
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/question.css"))
        frag.add_javascript_url("https://cdn.jsdelivr.net/gh/vast-engineering/jquery-popup-overlay@2/jquery.popupoverlay.min.js")
        frag.add_javascript(self.resource_string("static/js/src/question.js"))
        frag.initialize_js('QuestionXBlock', json_args=self.get_context())
        return frag

    @XBlock.json_handler
    def get_data(self, somedata, sufix=''):
        return self.data

    @XBlock.json_handler
    def submit(self, data, suffix=''):
        user_answers = []
        correct = False
        answers = data.get("answers")
        try:
            self.user_confidence = int(data.get("confidence"))
        except ValueError:
            self.user_confidence = None

        if self.question.get('type') == "number":
            for answer in answers:
                try:
                    user_answer = float(answer.get('value'))
                    user_answers.append(user_answer)
                    correct_answer = self.answer
                    if correct_answer - self.preciseness <= user_answer <= correct_answer + self.preciseness:
                        correct = True
                except ValueError:
                    user_answer = None

        elif self.question.get('type') == "text":
            for answer in answers:
                user_answers.append(answer.get('value'))
                if answer.get('value') == self.answer:
                    correct = True

        elif self.question.get('type') in ["select", "radio", "checkbox"]:
            correct_answers = [ option["title"] for option in self.options if option["correct"] is True ]
            for answer in answers:
                user_answers.append(answer.get('value'))
            if set(user_answers) == set(correct_answers):
                correct = True

        grade_value = 1 if correct else 0
        self.runtime.publish(self, 'grade', {'value': grade_value, 'max_value': 1})
        self.user_answer = user_answers
        return correct
