import aws_cdk as core
import aws_cdk.assertions as assertions

from automated_tcm.automated_tcm_stack import AutomatedTcmStack

# example tests. To run these tests, uncomment this file along with the example
# resource in automated_tcm/automated_tcm_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AutomatedTcmStack(app, "automated-tcm")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
