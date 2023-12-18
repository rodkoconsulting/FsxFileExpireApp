import unittest
from FsxFileExpire import app
import smbclient

PARAMETER_STORE_KEY = '/fsx/credentials/share'
ASSERT_CREDENTIALS_KEY = 'username'
REPORT_COUNT = 11


class IntegrationTestHandlerCase(unittest.TestCase):
    def test_response(self):
        print("Testing calls from lambda function")
        credentials_json = app.get_credentials_from_parameter_store(PARAMETER_STORE_KEY)
        self.assertIn(ASSERT_CREDENTIALS_KEY, credentials_json, "bad data returned from parameter store")
        credentials = app.get_credentials_from_json(credentials_json)
        self.assertIsInstance(credentials, tuple, "tuple not returned from credentials json")
        report_list = app.create_report_list()
        smbclient.register_session(server=credentials.host, username=credentials.username,
                                   password=credentials.password)
        app.process_reports(report_list, credentials)
        smbclient.reset_connection_cache()


if __name__ == '__main__':
    unittest.main()
