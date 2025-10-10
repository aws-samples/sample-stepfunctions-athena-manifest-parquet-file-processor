# Orchestrating big data processing with AWS Step Functions Distributed Map

This sample application demonstrates IoT sensor data analytics using AWS Step Functions Distributed Map with Athena manifest and Parquet file processing.

## Table of Contents

- [Workflow](#workflow)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Cleanup](#cleanup)
- [License](#license)

## Workflow

The following diagram shows the Step Functions workflow.

![AWS Step Function workflow](images/stepfunctions-workflow.png)

- AWS Step Functions: Orchestrates distributed processing using Distributed Map
- AWS Lambda Function: Processes individual sensor readings and detects anomalies
- Amazon DynamoDB: Stores processed sensor summaries
- Amazon S3: Stores raw Parquet data and analytics results

The system detects the following as anomalies:

- Temperature spikes (>35°C or <-10°C)
- Humidity anomalies (>95% or <5%)
- Low battery conditions (<20%)

## Prerequisites

- [Create an AWS account](https://portal.aws.amazon.com/gp/aws/developer/registration/index.html) if you do not already have one and log in.
- Have access to an AWS account through the AWS Management Console and the [AWS Command Line Interface (AWS CLI)](https://aws.amazon.com/cli). The [AWS Identity and Access Management (IAM)](https://aws.amazon.com/iam) user that you use must have permissions to make the necessary AWS service calls and manage AWS resources mentioned in this post. While providing permissions to the IAM user, follow the [principle of least-privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege).
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) installed and configured
- [Git Installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [AWS Serverless Application Model](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) (AWS SAM) installed
- Python 3.13+ installed

## Quick Start

### 1. Clone and navigate to stacks directory (all commands run from here)

Clone the GitHub repository in a new folder and navigate to project root folder:
```bash
git clone TODO
cd sample-stepfunctions-json-array-processor
```

### 2. Install Python dependencies

Run the following command to install Python dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install -r requirements.txt
   ```

### 3. Build and deploy the application

Run the following commands to build and deploy the application

   ```bash
   sam build
   sam deploy --guided
   ```

Enter the following details:
- Stack name: The CloudFormation stack name(for example, stepfunctions-athena-manifest-parquet-file-processor)
- AWS Region: A supported AWS Region (for example, us-east-1)
- Keep rest of the components to default values.

The outputs from the `sam deploy` will be used in the subsequent steps. 

### 4. Generate the test data and upload it to S3 bucket

You can use the Athena manifest files, generated from UNLOAD query results. When running an UNLOAD query, Athena generates a data manifest file in addition to the actual data objects. The manifest file provides a structured CSV list of the data files. Both the manifest and the data files are saved to your Athena query result location in Amazon S3.
For this demonstration, you’ll generate the Athena manifest and Parquet data file using a Python script. 

Run the following command to generate sample test data and upload it to the input S3 bucket. Replace `IoTDataBucketName` with the value from `sam deploy` output.

   ```bash
   python3 scripts/generate_sample_data.py <IoTDataBucketName>
   ```

### 5. Test the Step Functions workflow

Run the following command to start execution of the Step Functions. Replace the `StateMachineArn` with the value from `sam deploy` output.

```bash
aws stepfunctions start-execution \
  --state-machine-arn <StateMachineArn> \
  --input '{}'
```

The Step Function statemachine reads the list of Parquet data files from the Athena manifest file and processes them in parallel.

### 6. Monitor the state machine execution

Run the following command to get the details of the execution. Replace the `executionArn` from the previous command.

```bash
aws stepfunctions describe-execution --execution-arn <executionArn>
```

Wait until you get the status  `SUCCEEDED`.

### 7. Verify Results

Run the following commands to check the processed output from `SensorSummaryTableName` DynamoDB table. Replace the value `SensorSummaryTableName` with the value from `sam deploy` output. 

```bash
aws dynamodb scan --table-name <SensorSummaryTableName>

```

Check that the IoT sensor data is saved into DynamoDB table. Also check the `HealthStatus` attribute value. If any of the data is beyond the threshold, then `HealthStatus` attribute will be set to `anomalies_detected`.

## Cleanup

Run the following commands to delete the resources deployed in this sample application.

1. **Delete S3 bucket contents:**

   ```bash
   aws s3 rm s3://<IoTDataBucketName> --recursive
   aws s3 rm s3://<IoTAnalyticsResultsBucketName> --recursive
   ```

2. **Delete the SAM stack:**

   ```bash
   sam delete
   ```
This library is licensed under the MIT-0 License. See the LICENSE file.

