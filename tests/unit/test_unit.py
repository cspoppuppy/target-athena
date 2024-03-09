import unittest
from nose.tools import assert_raises

from target_athena.utils import get_target_key


class TestUnit(unittest.TestCase):
    """
    Unit Tests
    """

    @classmethod
    def setUp(self):
        self.config = {}

    def test_naming_convention_replaces_tokens(self):
        """Test that the naming_convention tokens are replaced"""
        stream_name = "the_stream"
        object_format = "csv"
        prefix = "test_"
        timestamp = "fake_timestamp"
        s3_key = get_target_key(
            stream_name=stream_name,
            object_format=object_format,
            prefix=prefix,
            timestamp=timestamp,
        )

        self.assertEqual("test_the_stream/fake_timestamp.csv", s3_key)

    def test_naming_convention_has_reasonable_default(self):
        """Test the default value of the naming convention"""
        stream_name = "the_stream"
        s3_key = get_target_key(stream_name)

        # default is "{stream}/{timestamp}.csv"
        self.assertTrue(s3_key.startswith(stream_name))
        self.assertTrue(s3_key.endswith(".jsonl"))
