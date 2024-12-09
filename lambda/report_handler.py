import base64
import json
import os

import boto3
import urllib.request
from urllib.error import URLError, HTTPError
import ssl

from logic_handler import (get_file_context, put_file_contents, datetime_int, render_docx_template)

def handler(event, context):
    ssl._create_default_https_context = ssl._create_unverified_context
    codepipeline = boto3.client('codepipeline')
    job_id = event['CodePipeline.job']['id']
    data = get_file_context()
    file_content = json.loads(data)
    # we should do our calculations and stuff before we render below this
    html_str = render_docx_template(file_content)
    report_name = 'mygovid_automated_tcm' + str(datetime_int()) + '.html'
    put_file_contents(html_str, report_name)
    # Encode the username and password
    credentials = f"{os.environ['ARTIFACTORY_SVC_USER']}:{os.environ['ARTIFACTORY_SVC_USER_TOKEN']}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    request = urllib.request.Request(
        os.environ['ARTIFACTORY_ENDPOINT'] + os.environ['ARTIFACTORY_REPO_STORAGE_PATH'] + report_name,
        data=str.encode(html_str),
        method='PUT')
    request.add_header('Authorization', f'Basic {encoded_credentials}')
    try:
        with urllib.request.urlopen(request) as response:
            response_data = response.read()
            print(response.getcode())
            print(response_data.decode('utf-8'))
    except HTTPError as e:
        print(f'HTTPError: {e.code} - {e.reason}')
        codepipeline.put_job_failure_result(jobId=job_id)
    except URLError as e:
        print(f'URLError: {e.reason}')
        codepipeline.put_job_failure_result(jobId=job_id)
    # we should clear the context here, so we won't need to do another lambda
    codepipeline.put_job_success_result(jobId=job_id)
