import base64
import io
import json
import os
from io import StringIO, BytesIO


def render_docx_template(context) -> bytes:
    from docxtpl import DocxTemplate
    doc = DocxTemplate("templates/myID_FT&PT_TCM_{Release}_{Year}.docx")
    doc.render(context)
    s_buf = io.BytesIO()
    doc.save(s_buf)
    s_buf.seek(0)
    data = s_buf.read()
    return data

def get_file_contents() -> dict:
    import boto3
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=os.environ['lambda_config'])
    file_content = response['Body'].read().decode('utf-8')
    return file_content

def get_zip_from_s3(Key="vssln.zip") -> BytesIO:
    from zipfile import ZipFile
    import boto3
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=Key)
    file_content = response.get('Body').read()
    trx_zip = ZipFile(BytesIO(file_content))
     # we assume the trx only has 1 file in the zip
    return trx_zip.open(trx_zip.namelist()[0]) # unzip the file

def get_file_context(Key="ss_test_run.trx") -> dict:
    import boto3
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=Key)
    print(response)
    file_content = response['Body'].read().decode('utf-8')
    return file_content


def datetime_int() -> int:
    # Importing datetime.
    from datetime import datetime
    a = datetime.now()
    a = int(a.strftime('%Y%m%d%s'))
    return a

def put_file_contents(buff: str, Key: str):
    import boto3
    s3bucket = boto3.client('s3')
    s3bucket.put_object(Body=buff, Bucket=os.environ['s3_bucket_reports'], Key=Key)
