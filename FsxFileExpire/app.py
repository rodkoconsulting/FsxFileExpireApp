import json
import boto3
import os, time, sys
import base64
import smbclient
from botocore.exceptions import ClientError
from pathlib import Path

from smbprotocol.exceptions import (
    SMBResponseException,
)


def lambda_handler(event, context):
    secret = get_secret("credentials-share")

    jsonString = json.loads(secret)
    username = jsonString["username"]
    password = jsonString["password"]
    host = jsonString["host"]
    destShare = jsonString["share"]
    basePath = "MAS_PDF/Sales_PDFExplode"
    njNobPath = "NJ NOB/PDFExplode"
    njDay6Path = "NJ DAY6/PDFExplode"
    nyNodPath = "NY NOD/PDFExplode"
    nyPastDuePath = "NY PAST DUE/PDFExplode"
    nyDay4Path = "NY DAY4/PDFExplode"
    nysTaxStatementsPath = "NYSTaxStatements"
    manifestPath = "Manifest"
    expMoboPath = "Exp MOBO"
    arAgingPastDueRepPath = "ArAgingPastDueRep"
    dailySalesPath = "DailySales"
    mtdSalesPath = "MtdSales"
    njNobDays = 1825
    nyNodDays = 730
    nyPastDueDays = 1
    nyDay4Days = 1
    nysTaxStatementsDays = 1
    manifestDays = 1
    njDay6Days = 1
    expMoboDays = 1
    arAgingPastDueRepDays = 1
    dailySalesDays = 1
    mtdSalesDays = 1
    now = time.time()

    reportList = [{}]
    reportList.append({njNobPath: njNobDays})
    reportList.append({njDay6Path: njDay6Days})
    reportList.append({nyNodPath: nyNodDays})
    reportList.append({nyPastDuePath: nyPastDueDays})
    reportList.append({nyDay4Path: nyDay4Days})
    reportList.append({nysTaxStatementsPath: nysTaxStatementsDays})
    reportList.append({manifestPath: manifestDays})
    reportList.append({expMoboPath: expMoboDays})
    reportList.append({arAgingPastDueRepPath: arAgingPastDueRepDays})
    reportList.append({dailySalesPath: dailySalesDays})
    reportList.append({mtdSalesPath: mtdSalesDays})

    try:
        print("Server: {}".format(host))
        print("User: {}".format(username))
        smbclient.register_session(server=host, username=username, password=password)
        print("SMB client registered")
    except SMBResponseException as exc:
        print("Error establishing session: {}".format(exc))

    for report in reportList:
        for subPath, expireDays in report.items():
            try:
                expireDate = now - expireDays * 86400
                directoryPath = os.path.join(host, destShare, basePath, subPath)
                for file_info in smbclient.scandir(directoryPath):
                    itemTime = file_info.stat().st_mtime
                    if file_info.is_file() and itemTime < expireDate:
                        smbclient.remove(os.path.join(directoryPath, file_info.name))
            except SMBResponseException as exc:
                ("Error deleting file: {}".format(exc))
                continue
    smbclient.reset_connection_cache()


def get_secret(secret_name):
    print("Starting get_secret")
    region_name = os.environ['AWS_REGION']
    print("Region: {}".format(region_name))
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        print("Starting get_secret_value_response")
        print("Secret name:{}".format(secret_name))
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        print("Complete get_secret_value_response")

    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret