"""
Tests for the testing Offline Mode tacks.
"""

from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx.features.offline_mode.constants import MAX_RETRY_ATTEMPTS, OFFLINE_SUPPORTED_XBLOCKS
from openedx.features.offline_mode.tasks import (
    generate_offline_content_for_block,
    generate_offline_content_for_course,
)
from xmodule.modulestore.exceptions import ItemNotFoundError


class GenerateOfflineContentTasksTestCase(TestCase):
    """
    Test case for the testing generating offline content tacks.
    """

    @patch('openedx.features.offline_mode.tasks.OfflineContentGenerator')
    @patch('openedx.features.offline_mode.tasks.modulestore')
    def test_generate_offline_content_for_block_success(
        self,
        modulestore_mock: MagicMock,
        offline_content_generator_mock: MagicMock,
    ) -> None:
        block_id_mock = 'block-v1:a+a+a+type@problem+block@fb81e4dbfd4945cb9318d6bc460a956c'
        html_data_mock = 'html_markup_data_mock'

        generate_offline_content_for_block(block_id_mock, html_data_mock)

        modulestore_mock.assert_called_once_with()
        modulestore_mock.return_value.get_item.assert_called_once_with(UsageKey.from_string(block_id_mock))
        offline_content_generator_mock.assert_called_once_with(
            modulestore_mock.return_value.get_item.return_value, html_data_mock
        )
        offline_content_generator_mock.return_value.generate_offline_content.assert_called_once_with()

    @patch('openedx.features.offline_mode.tasks.OfflineContentGenerator')
    @patch('openedx.features.offline_mode.tasks.modulestore', side_effect=ItemNotFoundError)
    def test_generate_offline_content_for_block_with_exception_in_modulestore(
        self,
        modulestore_mock: MagicMock,
        offline_content_generator_mock: MagicMock,
    ) -> None:
        block_id_mock = 'block-v1:a+a+a+type@problem+block@fb81e4dbfd4945cb9318d6bc460a956c'
        html_data_mock = 'html_markup_data_mock'

        generate_offline_content_for_block.delay(block_id_mock, html_data_mock)

        self.assertEqual(modulestore_mock.call_count, MAX_RETRY_ATTEMPTS + 1)
        offline_content_generator_mock.assert_not_called()

    @patch('openedx.features.offline_mode.tasks.OfflineContentGenerator', side_effect=FileNotFoundError)
    @patch('openedx.features.offline_mode.tasks.modulestore')
    def test_generate_offline_content_for_block_with_exception_in_offline_content_generation(
        self,
        modulestore_mock: MagicMock,
        offline_content_generator_mock: MagicMock,
    ) -> None:
        block_id_mock = 'block-v1:a+a+a+type@problem+block@fb81e4dbfd4945cb9318d6bc460a956c'
        html_data_mock = 'html_markup_data_mock'

        generate_offline_content_for_block.delay(block_id_mock, html_data_mock)

        self.assertEqual(modulestore_mock.call_count, MAX_RETRY_ATTEMPTS + 1)
        self.assertEqual(offline_content_generator_mock.call_count, MAX_RETRY_ATTEMPTS + 1)

    @patch('openedx.features.offline_mode.tasks.generate_offline_content_for_block')
    @patch('openedx.features.offline_mode.tasks.XBlockRenderer')
    @patch('openedx.features.offline_mode.tasks.modulestore')
    def test_generate_offline_content_for_course_supported_block_types(
        self,
        modulestore_mock: MagicMock,
        xblock_renderer_mock: MagicMock,
        generate_offline_content_for_block_mock: MagicMock,
    ) -> None:
        course_id_mock = 'course-v1:a+a+a'
        xblock_location_mock = 'xblock_location_mock'
        html_data_mock = 'html_markup_data_mock'
        modulestore_mock.return_value.get_items.return_value = [
            Mock(location=xblock_location_mock, closed=Mock(return_value=False))
        ]
        xblock_renderer_mock.return_value.render_xblock_from_lms.return_value = html_data_mock
        expected_call_args_for_modulestore_get_items = [
            call(CourseKey.from_string(course_id_mock), qualifiers={'category': offline_supported_block_type})
            for offline_supported_block_type in OFFLINE_SUPPORTED_XBLOCKS
        ]
        expected_call_args_for_xblock_renderer_mock = [
            call(xblock_location_mock) for _ in OFFLINE_SUPPORTED_XBLOCKS
        ]
        expected_call_args_for_generate_offline_content_for_block_mock = [
            call([xblock_location_mock, html_data_mock]) for _ in OFFLINE_SUPPORTED_XBLOCKS
        ]

        generate_offline_content_for_course(course_id_mock)

        self.assertEqual(modulestore_mock.call_count, len(OFFLINE_SUPPORTED_XBLOCKS))
        self.assertListEqual(
            modulestore_mock.return_value.get_items.call_args_list, expected_call_args_for_modulestore_get_items
        )
        self.assertListEqual(
            xblock_renderer_mock.call_args_list, expected_call_args_for_xblock_renderer_mock
        )
        self.assertListEqual(
            generate_offline_content_for_block_mock.apply_async.call_args_list,
            expected_call_args_for_generate_offline_content_for_block_mock
        )

    @patch('openedx.features.offline_mode.tasks.generate_offline_content_for_block')
    @patch('openedx.features.offline_mode.tasks.XBlockRenderer')
    @patch('openedx.features.offline_mode.tasks.modulestore')
    def test_generate_offline_content_for_course_supported_block_types_closed_xblock(
        self,
        modulestore_mock: MagicMock,
        xblock_renderer_mock: MagicMock,
        generate_offline_content_for_block_mock: MagicMock,
    ) -> None:
        course_id_mock = 'course-v1:a+a+a'
        xblock_location_mock = 'xblock_location_mock'
        html_data_mock = 'html_markup_data_mock'
        modulestore_mock.return_value.get_items.return_value = [
            Mock(location=xblock_location_mock, closed=Mock(return_value=True))
        ]
        xblock_renderer_mock.return_value.render_xblock_from_lms.return_value = html_data_mock
        expected_call_args_for_modulestore_get_items = [
            call(CourseKey.from_string(course_id_mock), qualifiers={'category': offline_supported_block_type})
            for offline_supported_block_type in OFFLINE_SUPPORTED_XBLOCKS
        ]

        generate_offline_content_for_course(course_id_mock)

        self.assertEqual(modulestore_mock.call_count, len(OFFLINE_SUPPORTED_XBLOCKS))
        self.assertListEqual(
            modulestore_mock.return_value.get_items.call_args_list, expected_call_args_for_modulestore_get_items
        )
        xblock_renderer_mock.assert_not_called()
        generate_offline_content_for_block_mock.assert_not_called()
