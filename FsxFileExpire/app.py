# Python
import json
import os
import time
from collections import namedtuple
import boto3
import smbclient
from smbprotocol.exceptions import SMBResponseException

PARAMETER_STORE_KEY = '/fsx/credentials/share'
PARAMETER_STORE_FUNCTION = 'ParameterStoreGetValueFunction_PROD'
BASE_PATH = 'MAS_PDF/Sales_PDFExplode'
REPORT_ITEMS = {
    "NJ_NOB": {"path": 'NJ NOB/PDFExplode', "days": 1825},
    "NJ_DAY6": {"path": 'NJ DAY6/PDFExplode', "days": 1},
    "NY_NOD": {"path": 'NY NOD/PDFExplode', "days": 730},
    "NY_PAST_DUE": {"path": 'NY PAST DUE/PDFExplode', "days": 1},
    "NY_DAY4": {"path": 'NY DAY4/PDFExplode', "days": 1},
    "NYS_TAX_STATEMENTS": {"path": 'NYSTaxStatements', "days": 1},
    "MANIFEST": {"path": 'Manifest', "days": 1},
    "EXP_MOBO": {"path": 'Exp MOBO', "days": 1},
    "AR_AGING_PAST_DUE_REP": {"path": 'Exp MOBO', "days": 1},
    "DAILY_SALES": {"path": 'DailySales', "days": 1},
    "MTD_SALES": {"path": 'MtdSales', "days": 1}
}
SECONDS_IN_DAY = 86400


def get_credentials_from_parameter_store(parameter):
    lambda_client = boto3.client('lambda')
    return lambda_client.invoke(FunctionName=PARAMETER_STORE_FUNCTION, InvocationType='RequestResponse',
                                Payload=json.dumps(parameter))


def get_credentials_from_json(credentials_json):
    json_string = json.loads(credentials_json)
    username = json_string["username"]
    password = json_string["password"]
    host = json_string["host"]
    share = json_string["share"]
    credentials = namedtuple('Credentials', 'username password host share')
    return credentials(username, password, host, share)


def get_expire_date(expire_days):
    return time.time() - expire_days * SECONDS_IN_DAY


def create_report_list():
    return [{value["path"]: value["days"]} for value in REPORT_ITEMS.values()]


def process_reports(report_list, credentials):
    for report in report_list:
        for sub_path, expire_days in report.items():
            directory_path = os.path.join(credentials.host, credentials.share, BASE_PATH, sub_path)
            try:
                expire_date = get_expire_date(expire_days)
                for file_info in smbclient.scandir(directory_path):
                    item_time = file_info.stat().st_mtime
                    is_file_old = file_info.is_file() and item_time < expire_date
                    if is_file_old:
                        smbclient.remove(os.path.join(directory_path, file_info.name))
            except SMBResponseException as exc:
                print(f"Error deleting file: {exc}")
                continue


def lambda_handler(event, context):
    credentials_json = get_credentials_from_parameter_store(PARAMETER_STORE_KEY)
    credentials = get_credentials_from_json(credentials_json)
    report_list = create_report_list()

    try:
        smbclient.register_session(server=credentials.host, username=credentials.username,
                                   password=credentials.password)
    except SMBResponseException as exc:
        print(f"Error establishing session: {exc}")
        return

    process_reports(report_list, credentials)

    smbclient.reset_connection_cache()
