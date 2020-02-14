"""TO-DO: Write a description of what this XBlock is."""
import pkg_resources
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.scorable import ScorableXBlockMixin
from xblock.fields import JSONField, Scope, Integer, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin


loader = ResourceLoader(__name__)

MAX_ALLOWED_SUBMISSON = 2


class QuestionXBlock(StudioEditableXBlockMixin, XBlock):
    """
    TO-DO: document what your XBlock does.
    """
    editable_fields = ('data',)
    has_score = True
    icon_class = 'problem'

    def get_icon_class(self):
        return self.icon_class

    display_name = String(default="Question")
    data = JSONField(default={})
    user_confidence = Integer(scope=Scope.user_state)
    user_answer = JSONField(scope=Scope.user_state, default='')
    submission_counter = Integer(scope=Scope.user_state, default=0)

    @property
    def img_urls(self):
        return self.data.get("imgUrls", [])

    @property
    def iframe_url(self):
        return self.data.get("iframeUrl")

    @property
    def description(self):
        return self.data.get("description")

    @property
    def problem_types(self):
        return self.data.get("problemTypes", [])

    def preciseness(self, problem_type):
        preciseness = problem_type.get("preciseness")
        preciseness_values = preciseness.split('%')
        try:
            preciseness_value = float(preciseness_values[0]) if preciseness_values else 0
        except ValueError:
            preciseness_value = 0

        if preciseness.rfind('%') > -1:
            return preciseness_value * float(problem_type['answer']) / 100
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

    @property
    def is_submission_allowed(self):
        return self.submission_counter < MAX_ALLOWED_SUBMISSON

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def get_context(self):
        return {
            "user_answer": self.user_answer,
            "is_submission_allowed": self.is_submission_allowed,
            "problem_types": self.problem_types,
            "img_urls": self.img_urls,
            "iframe_url": self.iframe_url,
            "description": self.description,
            "confidence_text": self.confidence_text,
            "correct_answer_text": self.correct_answer_text,
            "incorrect_answer_text": self.incorrect_answer_text,
            "rephrase": self.rephrase,
            "break_down": self.break_down,
            "teach_me": self.teach_me,
            'location_id': self.location.block_id
        }

    def student_view(self, context=None):
        """
        The primary view of the QuestionXBlock, shown to students
        when viewing courses.
        """
        context = self.get_context()
        html = loader.render_mako_template(
            'static/html/question.html',
            context=context
        )
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/question.css"))
        frag.add_javascript(self.resource_string("static/js/src/question.js"))

        frag.initialize_js('QuestionXBlock', json_args=context)
        return frag

    @XBlock.json_handler
    def get_data(self, somedata, sufix=''):
        return self.data

    @XBlock.json_handler
    def submit(self, data, suffix=''):
        answers = data.get("answers")
        self.submission_counter += 1
        try:
            user_confidence = int(data.get("confidence"))
        except ValueError:
            user_confidence = None

        user_answers = []

        for index, question in enumerate(self.problem_types):

            if question['type'] == "number":
                answer = False
                if answers[index][0]:
                    try:
                        temp_answer = float(answers[index][0])
                        correct_answer = float(question['answer'])
                        preciseness = self.preciseness(question)
                        answer = correct_answer - preciseness <= temp_answer <= correct_answer + preciseness
                    except ValueError:
                        pass
                user_answers.append(answer)

            elif question['type'] == "text":
                answer = answers[index][0].replace(' ', '') == question['answer'].replace(' ', '')
                user_answers.append(answer)

            elif question['type'] in ["select", "radio", "checkbox"]:
                correct_answers = [option["title"] for option in question['options'] if option["correct"]]
                answer = set(answers[index]) == set(correct_answers)
                user_answers.append(answer)

            elif question['type'] == "table":
                correct_answers = []
                for row in question['tableData'].get('rows', []):
                    correct_answers += [
                        val['value'].replace('?', '', 1) for key, val in row.items() if val['value'].startswith('?')
                    ]
                answer = set(answers[index]) == set(correct_answers)
                user_answers.append(answer)

        result_answer = all(user_answers)

        grade_value = 1 if result_answer else 0

        self.runtime.publish(self, 'grade', {'value': grade_value, 'max_value': 1})
        self.user_answer = answers
        self.user_confidence = user_confidence
        return {
            'correct': result_answer,
            'is_submission_allowed': self.is_submission_allowed
        }

    @XBlock.json_handler
    def skip(self, somedata, sufix=''):
        self.submission_counter += 1
        return {'is_submission_allowed': self.is_submission_allowed}
