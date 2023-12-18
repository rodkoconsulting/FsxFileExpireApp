import unittest
from FsxFileExpire import app

REPORT_COUNT = 11


class UnitTestHandlerCase(unittest.TestCase):
    def test_response(self):
        print("Testing calls to lambda function")
        report_list = app.create_report_list()
        self.assertIs(report_list.count(), REPORT_COUNT, "report list not returning correct count")


if __name__ == '__main__':
    unittest.main()
