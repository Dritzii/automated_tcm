import base64
import io
import json
import os


def render_docx_template(context):
    from docxtpl import DocxTemplate
    doc = DocxTemplate("/templates/myID_FT&PT_TCM_{Release}_{Year}.docx")
    doc.render(context)
    doc.save("generated_doc.docx")

def get_file_contents() -> dict:
    import boto3
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=os.environ['lambda_config'])
    file_content = response['Body'].read().decode('utf-8')
    return file_content


def get_file_context(Key="ss_test_run.trx") -> dict:
    import boto3
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=Key)
    file_content = response['Body'].read().decode('utf-8')
    return file_content


def datetime_int() -> int:
    # Importing datetime.
    from datetime import datetime
    a = datetime.now()
    a = int(a.strftime('%Y%m%d%s'))
    return a

def put_file_contents(buff: str, Key: str):
    s3bucket = boto3.client('s3')
    s3bucket.put_object(Body=buff, Bucket=os.environ['s3_bucket_reports'], Key=Key)

