from aws_cdk import (
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    Duration,
    Stack,
    CfnParameter,
    CfnOutput,
    RemovalPolicy,
    aws_logs as logs
)
from constructs import Construct

class TranscriptCollectorProjectStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define an environment parameter
        env_param = CfnParameter(
            self, "Environment",
            type="String",
            description="The deployment environment (e.g., dev, staging, prod)",
            default="dev"
        )

        # Define a parameter for the SageMaker execution role ARN
        sagemaker_execution_role_arn_param = CfnParameter(
            self, "SageMakerExecutionRoleARN",
            type="String",
            description="The ARN of the SageMaker execution role"
        )

        environment = env_param.value_as_string
        sagemaker_execution_role_arn = sagemaker_execution_role_arn_param.value_as_string

        # Create an S3 bucket with an environment-specific name
        s3_bucket = s3.Bucket(
            self, 'TranscriptCollectorBucket',
            bucket_name=f'transcript-collector-bucket-{environment}',
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create a DynamoDB table with an environment-specific name
        dynamodb_table = dynamodb.Table(
            self, 'TranscriptCollectorTable',
            table_name=f'TranscriptCollectorTable-{environment}',
            partition_key=dynamodb.Attribute(
                name='video_id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # AWS Lambda function with a custom name and environment variables
        lambda_function = lambda_.Function(
            self, 'TranscriptCollectorFunction',
            function_name=f'TranscriptCollectorFunction-{environment}',
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler='transcript_collector.lambda_handler',
            code=lambda_.Code.from_asset('lambda'),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                'BUCKET_NAME': s3_bucket.bucket_name,
                'DYNAMODB_TABLE_NAME': dynamodb_table.table_name
            },
            log_retention=logs.RetentionDays.ONE_MONTH
        )

        # Adding AWS Data Wrangler Layer using ARN for eu-central-1
        aws_data_wrangler_layer = lambda_.LayerVersion.from_layer_version_arn(
            self, 'AWSDataWranglerLayer',
            'arn:aws:lambda:eu-central-1:336392948345:layer:AWSSDKPandas-Python310:16'
        )

        # Adding custom layer for pytubefix using the local zip file
        pytubefix_layer = lambda_.LayerVersion(
            self, 'PytubefixLayer',
            layer_version_name=f'PytubefixLayer-{environment}',
            code=lambda_.Code.from_asset('lambda/pytubefix_layer.zip'),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_10],
            description='Layer containing pytubefix library'
        )

        # Attach the layers to the Lambda function
        lambda_function.add_layers(aws_data_wrangler_layer, pytubefix_layer)

        # Grant the Lambda function permissions to access the S3 bucket
        s3_bucket.grant_read_write(lambda_function)

        # Grant the Lambda function permissions to access the DynamoDB table
        dynamodb_table.grant_read_write_data(lambda_function)

        # Create an IAM role for accessing resources from SageMaker
        sagemaker_role = iam.Role(
            self, 'SageMakerAccessRole',
            assumed_by=iam.ArnPrincipal(sagemaker_execution_role_arn),
            inline_policies={
                'SageMakerAccessPolicy': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:ListBucket",
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject"
                            ],
                            resources=[s3_bucket.bucket_arn, f"{s3_bucket.bucket_arn}/*"]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:GetItem",
                                "dynamodb:Scan",
                                "dynamodb:Query"
                            ],
                            resources=[dynamodb_table.table_arn]
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "lambda:InvokeFunction",
                                "lambda:InvokeAsync"
                            ],
                            resources=[lambda_function.function_arn]
                        )
                    ]
                )
            }
        )

        # Output the role ARN
        CfnOutput(self, "SageMakerRoleARN", value=sagemaker_role.role_arn)
