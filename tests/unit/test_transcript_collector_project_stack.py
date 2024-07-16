import aws_cdk as core
import aws_cdk.assertions as assertions

from transcript_collector_project.transcript_collector_project_stack import TranscriptCollectorProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in transcript_collector_project/transcript_collector_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = TranscriptCollectorProjectStack(app, "transcript-collector-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
