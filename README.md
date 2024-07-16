
# Welcome to Your CDK Python Project

This project is designed for CDK development with Python. Its primary objective is to extract captions from YouTube videos, process them, and store the resulting transcripts and metadata in AWS services, such as S3 and DynamoDB.
It currently uses [pytubefix](https://pytubefix.readthedocs.io/en/latest/) (contained as a layer for deployment) to fetch transcripts/metadata. I added a jupyter nobebook with some examples to scrape entire channels/videos.

Below is a guide to help you set up and deploy the project.

## Installing Dependencies

Once the virtual environment is activated, install the required dependencies using Poetry.

```sh
$ poetry install --with dev
```

## Making the Kernel Accessible to Jupyter

To make the Python environment accessible in Jupyter, run the following command:

```sh
$ python -m ipykernel install --user --name=transcriptcollector --display-name "Python (transcriptcollector)"
```

## Deploying to a Stage and Creating a Role

This role is created to have access to the created ressources (dynamodb, s3 bucket, lambda invocation). Ensure you replace the placeholders with your own values.

```sh
$ cdk deploy --parameters Environment=<your_environment> --parameters SageMakerExecutionRoleARN=<your_role_arn>
```

## Useful Commands

 * `cdk ls`          List all stacks in the app
 * `cdk synth`       Emit the synthesized CloudFormation template
 * `cdk deploy`      Deploy this stack to your default AWS account/region
 * `cdk diff`        Compare deployed stack with the current state
 * `cdk docs`        Open CDK documentation

