import os
import botocore
import unittest

from nose.tools import assert_raises

from target_athena.target import TargetAthena
from target_athena import s3
from dotenv import load_dotenv

from tests.integration.utils import get_test_config, get_test_tap_lines


load_dotenv()  # take environment variables from .env.


class TestIntegration(unittest.TestCase):
    """
    Integration Tests
    """

    maxDiff = None

    def setUp(self):
        self.config = get_test_config()
        self.s3_client = s3.create_client(self.config)

    def assert_three_streams_are_in_s3_bucket(
        self,
        should_metadata_columns_exist=False,
        should_hard_deleted_rows=False,
        compression=None,
        delimiter=",",
        quotechar='"',
    ):
        """
        This is a helper assertion that checks if every data from the message-with-three-streams.json
        file is available in S3.
        Useful to check different loading methods (compressed, encrypted, custom delimiter and quotechar, etc.)
        without duplicating assertions
        """
        # TODO: This assertion function is currently a template and not implemented
        #       Here We should download files from S3 and compare to expected results based on the input
        #       parameters
        self.assertTrue(True)

    def persist_messages(self, messages):
        """Load data into S3"""
        target = TargetAthena(config=self.config, parse_env_config=True)
        target._process_lines(messages)

    def test_invalid_json(self):
        """Receiving invalid JSONs should raise an exception"""
        tap_lines = get_test_tap_lines("invalid-json.json")
        with assert_raises(Exception):
            self.persist_messages(tap_lines)

    def test_message_order(self):
        """RECORD message without a previously received SCHEMA message should raise an exception"""
        tap_lines = get_test_tap_lines("invalid-message-order.json")
        with assert_raises(Exception):
            self.persist_messages(tap_lines)

    def test_loading_csv_files(self):
        """Loading multiple tables from the same input tap with various columns types"""
        tap_lines = get_test_tap_lines("messages-with-three-streams.json")

        self.persist_messages(tap_lines)
        self.assert_three_streams_are_in_s3_bucket()

    # def test_aws_env_vars(self):
    #     """Test loading data with credentials defined in AWS environment variables
    #     rather than explicitly provided access keys"""
    #     tap_lines = get_test_tap_lines('messages-with-three-streams.json')
    #     try:
    #         # Move aws access key and secret from config into environment variables
    #         os.environ['AWS_ACCESS_KEY_ID'] = os.environ.get('TARGET_ATHENA_ACCESS_KEY_ID')
    #         os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ.get('TARGET_ATHENA_SECRET_ACCESS_KEY')

    #         config_aws_env_vars = self.config.copy()
    #         config_aws_env_vars['aws_access_key_id'] = None
    #         config_aws_env_vars['aws_secret_access_key'] = None

    #         # Create a new S3 client using env vars
    #         self.persist_messages(tap_lines)
    #         self.assert_three_streams_are_in_s3_bucket()
    #     # Delete temporary env var to not confuse other tests
    #     finally:
    #         del os.environ['AWS_ACCESS_KEY_ID']
    #         del os.environ['AWS_SECRET_ACCESS_KEY']

    def test_profile_based_auth(self):
        """Test AWS profile based authentication rather than access keys"""
        # Profile name given in config
        config_aws_profile = {"aws_profile": "fake_profile"}
        with self.assertRaises(botocore.exceptions.ProfileNotFound):
            s3.create_client(config_aws_profile)

    def test_profile_based_auth_aws_env_var(self):
        """Test AWS profile based authentication using AWS environment variables"""
        try:
            # Profile name defined as env var and config is empty
            os.environ["AWS_PROFILE"] = "fake_profile"
            config_aws_profile_env_vars = {}
            with self.assertRaises(botocore.exceptions.ProfileNotFound):
                s3.create_client(config_aws_profile_env_vars)
        # Delete temporary env var to not confuse other tests
        finally:
            del os.environ["AWS_PROFILE"]

    def test_loading_csv_files_with_gzip_compression(self):
        """Loading multiple tables from the same input tap with gzip compression"""
        tap_lines = get_test_tap_lines("messages-with-three-streams.json")

        # Turning on gzip compression
        self.config["compression"] = "gzip"
        self.persist_messages(tap_lines)
        self.assert_three_streams_are_in_s3_bucket(compression="gzip")

    def test_loading_csv_files_with_invalid_compression(self):
        """Loading multiple tables from the same input tap with invalid compression"""
        tap_lines = get_test_tap_lines("messages-with-three-streams.json")

        # Turning on a not supported compression method
        self.config["compression"] = "INVALID_COMPRESSION_METHOD"

        # Invalid compression method should raise exception
        with assert_raises(Exception):
            self._validate_config(raise_errors=True)

    # def test_naming_convention(self):
    #     tap_lines = get_test_tap_lines("messages-with-three-streams.json")

    #     self.config["naming_convention"] = "tester/{stream}/{timestamp}.csv"
    #     self.persist_messages(tap_lines)
    #     self.assert_three_streams_are_in_s3_bucket()

    def test_loading_tables_with_custom_temp_dir(self):
        """Loading multiple tables from the same input tap using custom temp directory"""
        tap_lines = get_test_tap_lines("messages-with-three-streams.json")

        # Use custom temp_dir
        self.config["temp_dir"] = "~/.pipelinewise/tmp"
        self.persist_messages(tap_lines)

        self.assert_three_streams_are_in_s3_bucket()
