import base64
import io
import json
import os

import boto3


def render_jinja_template(context):
    from jinja2 import Environment, select_autoescape, FileSystemLoader
    """
    Render a Jinja2 template from a template string and a context.

    Parameters:
    - template_string (str): The Jinja2 template string.
    - context (dict): The context to be used for rendering the template.

    Returns:
    - str: Rendered HTML content.
    """
    try:
        env = Environment(loader=FileSystemLoader(
            searchpath="./templates/"), autoescape=select_autoescape(['html']))
        template = env.get_template('report_template.html')
        rendered_html = template.render(context)
        return rendered_html
    except Exception as e:
        print(f"Error rendering template: {e}")
        return None


def _update_json() -> dict:
    return {'piechart_context': {"Successful": 0, "Failed": 0, "Planned": 0, "Executed": 0, "Passed": 0, "Skipped": 0},
            'reason_object': {}}


def render_html_template(context):
    rendered_html = render_jinja_template(context)
    return rendered_html


def get_png_image() -> io.BytesIO:
    with open("templates/ato.png", "rb") as logo:
        logo_stream = io.BytesIO(base64.b64encode(logo.read()))
        return logo_stream


def check_if_file_exists_lambda() -> bool:
    try:
        s3bucket = boto3.client('s3')
        s3bucket.head_object(Bucket=os.environ['s3_bucket'], Key=os.environ['lambda_config'])
        return True
    except Exception:
        return False


def get_file_contents() -> dict:
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=os.environ['lambda_config'])
    file_content = response['Body'].read().decode('utf-8')
    return file_content


def update_file_context(key: str, value: str, successful=False, failed=False, planned=False, Executed=False,
                        skipped=False, Passed=False):
    s3bucket = boto3.client('s3')
    updateJson = _update_json()
    try:
        response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key="htmlcontext.json")
        file_content = response['Body'].read().decode('utf-8')
        if file_content:
            file_content = json.loads(file_content)
            for k, v in file_content.items():
                updateJson[k] = v
                updateJson[key] = value
            if successful:
                updateJson['piechart_context']['Successful'] += 1
            if failed:
                updateJson['piechart_context']['Failed'] += 1
            if planned:
                updateJson['piechart_context']['Planned'] += 1
            if Executed:
                updateJson['piechart_context']['Executed'] += 1
            if skipped:
                updateJson['piechart_context']['Skipped'] += 1
            if Passed:
                updateJson['piechart_context']['Passed'] += 1
        put_file_contents(json.dumps(updateJson), "htmlcontext.json")
        return
    except Exception as e:
        print(e)
        # should give us no such key error if there is no file at the location
        # we would then create a brand new context file
        updateJson[key] = value
        put_file_contents(json.dumps(updateJson), "htmlcontext.json")
        return


def get_file_context(Key="htmlcontext.json") -> dict:
    s3bucket = boto3.client('s3')
    response = s3bucket.get_object(Bucket=os.environ['s3_bucket'], Key=Key)
    file_content = response['Body'].read().decode('utf-8')
    # file_content = json.loads(file_content)
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


def no_lambda_found():
    update_file_context(key="lambda_list",
                        value={"lambda_name": "null",
                               "successful": "No Lambda Function provided for invocation",
                               "response": "null",
                               "errortype": "null", "execution_time": "null"})
    update_file_context(key="reason_object",
                        value={
                            "Lambda_reason": "No Lambda Function was found - please make sure that your lambda function has the name/word -test- inside the stack or provided"},
                        skipped=True, Executed=True,
                        planned=True)


def invoke_lambda(lambda_name) -> dict:
    import time
    start = time.time()
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName=lambda_name,
        InvocationType="RequestResponse",
        # Payload=json.dumps(file_name)
    )
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        result = json.loads(response["Payload"].read())
        # successful
        # {'ResponseMetadata': {'RequestId': '9108e566-04f3-4055-ad62-6a28869829c3', 'HTTPStatusCode': 200, 'HTTPHeaders': {'date': 'Fri, 24 Nov 2023 03:55:18 GMT', 'content-type': 'application/json', 'content-length': '44', 'connection': 'keep-alive', 'x-amzn-requestid': '9108e566-04f3-4055-ad62-6a28869829c3', 'x-amzn-remapped-content-length': '0', 'x-amz-executed-version': '$LATEST', 'x-amzn-trace-id': 'root=1-65601ea1-3f8e14cd6ebf02a1163d53db;parent=64908a7c5772bfdd;sampled=0;lineage=bfe7b654:0|4f28d930:0'}, 'RetryAttempts': 0}, 'StatusCode': 200, 'ExecutedVersion': '$LATEST', 'Payload': <botocore.response.StreamingBody object at 0x7fec17e74df0>}
        # {'errorMessage': "Unable to import module 'lambda_handler': No module named 'lambda_handler'", 'errorType': 'Runtime.ImportModuleError', 'requestId': 'c67f6b1a-6473-4ef9-b962-ecb41a8c0208', 'stackTrace': []}
        if "errorMessage" in result:
            end = time.time()
            return {"lambda_name": lambda_name, "successful": False, "response": result['errorMessage'],
                    "errortype": result['errorType'], "execution_time": end - start}
        else:
            end = time.time()
            return {"lambda_name": lambda_name, "successful": True, "response": result,
                    "errortype": "No Errors Returned",
                    "execution_time": end - start}


def context_designer(**kwargs) -> dict:
    return {
        kwargs.get('key'): kwargs.get('value')
    }


def send_sns_topic(message) -> None:
    sns = boto3.client('sns')
    sns.publish(
        TargetArn=os.environ['target_arn'],
        Message=message,
        MessageStructure='text',
        Subject="Errors have occured in the lambda invoke stage"
    )


def iter_lambda_invoke(returned_list) -> None:
    for each in returned_list:
        if not each[0]:
            send_sns_topic(message_handler(returned_list))
        else:
            continue


def message_handler(returned_list) -> str:
    for each in returned_list:
        return f"""
        Test Pipeline Lambda Output

        Lambda name {each[3]} has returned a message of the below after an invocation
        {each[1]}


        Table Results:


        """
