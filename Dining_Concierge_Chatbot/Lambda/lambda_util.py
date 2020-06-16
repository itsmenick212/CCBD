
import json
import logging
import os
import time
import zipfile
import zlib
import boto3
from botocore.exceptions import ClientError


def get_iam_role_arn(iam_role_name):
    """Retrieve the ARN of an IAM role
    :param iam_role_name: IAM role name
    :return: If the IAM role exists, return ARN, else None
    """

    # Try to retrieve information about the role
    iam_client = boto3.client('iam')
    try:
        result = iam_client.get_role(RoleName=iam_role_name)
    except ClientError as e:
        logging.error(e)
        return None
    return result['Role']['Arn']


def iam_role_exists(iam_role_name):
    """Determine whether the specified IAM role exists
    :param iam_role_name: IAM role name
    :return: True if IAM role exists, else False
    """

    # Try to retrieve information about the role
    if get_iam_role_arn(iam_role_name) is None:
        return False
    return True


def create_iam_role_for_lambda(iam_role_name,policies):
    """Create an IAM role to enable a Lambda function to call AWS services
    :param iam_role_name: Name of IAM role
    :return: ARN of IAM role. If error, returns None.
    """

    # Lambda trusted relationship policy document
    lambda_assume_role = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': '',
                'Effect': 'Allow',
                'Principal': {
                    'Service': 'lambda.amazonaws.com'
                },
                'Action': 'sts:AssumeRole'
            }
        ]
    }
    iam_client = boto3.client('iam')
    try:
        result = iam_client.create_role(RoleName=iam_role_name,
                                        AssumeRolePolicyDocument=json.dumps(lambda_assume_role))
    except ClientError as e:
        logging.error(e)
        return None
    lambda_role_arn = result['Role']['Arn']

    # Attach the AWSLambdaBasicExecutionRole policy to the role
    # If planning to use AWS X-Ray, also attach the AWSXrayWriteOnlyAccess policy


    for policy in policies:
         try:
            iam_client.attach_role_policy(RoleName=iam_role_name,
                                      PolicyArn=policy)
         except ClientError as e:
            logging.error(e)
            return None

    '''
    # Debug: Verify policy is attached to the role
    try:
        response = iam_client.list_attached_role_policies(RoleName=iam_role_name)
    except ClientError as e:
        logging.error(e)
    else:
        for policy in response['AttachedPolicies']:
            logging.debug(f'Role: {iam_role_name}, '
                          f'Attached Policy: {policy["PolicyName"]}, '
                          f'ARN: {policy["PolicyArn"]}')
    '''

    # Return the ARN of the created IAM role
    return lambda_role_arn


def delete_iam_role(role_name):
    """Detach all managed policies from an IAM role and delete the role
    :param role_name: String name of IAM role to delete
    """

    # Retrieve all policies attached to the role
    iam_client = boto3.client('iam')
    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
    except ClientError as e:
        logging.error(e)
        return

    # Detach each policy
    while True:
        for policy in response['AttachedPolicies']:
            try:
                iam_client.detach_role_policy(RoleName=role_name,
                                              PolicyArn=policy['PolicyArn'])
            except ClientError as e:
                logging.error(e)
                # Process next attached policy

        # Is there another batch of policies?
        if response['IsTruncated']:
            # Get another batch
            try:
                response = iam_client.list_attached_role_policies(Marker=response['Marker'])
            except ClientError as e:
                logging.error(e)
                break
        else:
            logging.info(f'Detached all policies from IAM role {role_name}')
            break

    # Delete the role
    try:
        iam_client.delete_role(RoleName=role_name)
    except ClientError as e:
        logging.error(e)
    else:
        logging.info(f'Deleted IAM role: {role_name}')


def create_lambda_deployment_package(srcfile, deployment_package):
    """Create a Lambda deployment package (ZIP file)
    :param srcfile: Lambda function source file
    :param deployment_package: Name of generated deployment package
    :return: True if deployment package created. Otherwise, False.
    """

    # Create the deployment package
    with zipfile.ZipFile(deployment_package, mode='w',
                         compression=zipfile.ZIP_DEFLATED,
                         compresslevel=zlib.Z_DEFAULT_COMPRESSION) as deploy_pkg:
        try:
            deploy_pkg.write(srcfile)
        except Exception as e:
            logging.error(e)
            return False
    return True


def deploy_lambda_function(name, iam_role, handler, deployment_package,
                           runtime, env_vars, region):
    """Deploy the Lambda function
    The function assumes the deployment package can be read into memory. If
    the package is large because it contains many dependencies, the function
    should be modified to upload the package to S3.
    :param name: Descriptive Lambda function name
    :param iam_role: IAM Lambda role
    :param handler: Name of Lambda handler function
    :param deployment_package: Name of deployment package
    :param runtime: Lambda runtime programming language
    :param env_vars: Environment variables for Lambda context
    :param region: Region to deploy the Lambda function
    :return: Dictionary containing information about the function, else None
    """

    # Load the deployment package into memory
    # Alternatively, upload it to S3
    with open(deployment_package, mode='rb') as pkg:
        deploy_pkg = pkg.read()

    # Create the Lambda function
    # Note: create_function() raises an InvalidParameterValueException if its
    # newly-created IAM role has not been replicated to the appropriate region
    # yet. To resolve this situation, the operation is retried several times.
    lambda_client = boto3.client('lambda', region_name=region)
    retry_time = 1  # number of seconds to sleep
    max_retry_time = 32
    while retry_time <= max_retry_time:
        try:
            result = lambda_client.create_function(FunctionName=name,
                                                   Runtime=runtime,
                                                   Role=iam_role,
                                                   Handler=handler,
                                                   Environment=env_vars,
                                                   Code={'ZipFile': deploy_pkg})
        except ClientError as e:
            logging.error(e)
            logging.error(f'IAM role ARN: {iam_role}')

            # If InvalidParameterValueException, retry a few times until the role
            # has replicated to all regions.
            if e.response['Error']['Code'] == 'InvalidParameterValueException':
                logging.error('Waiting for IAM role to replicate to all regions,'
                              ' then retrying...')
                time.sleep(retry_time)
                retry_time *= 2
            else:
                return None
        else:
            return result
    return None


def create_lambda_function(function_name, srcfile, handler_name, role_name,
                           region, env_vars={}):
    """Create a Lambda function
    It is assumed that srcfile includes an extension, such as source.py or
    source.js. The filename minus the extension is used to construct the
    ZIP file deployment package, e.g., source.zip
    If the role_name exists, the existing role is used. Otherwise, an
    appropriate role is created.
    :param function_name: Lambda function name
    :param srcfile: Lambda source file
    :param handler_name: Lambda handler name
    :param role_name: Lambda role name
    :param region: Region to locate the Lambda resource
    :param env_vars: Dict of environment variables for Lambda context
    :return: String ARN of the created Lambda function. If error, returns None.
    """

    # Parse the filename and extension in srcfile
    filename, ext = os.path.splitext(srcfile)

    # Create a deployment package
    deployment_package = f'{filename}.zip'
    if not create_lambda_deployment_package(srcfile, deployment_package):
        return None

    # Create Lambda IAM role if necessary
    if iam_role_exists(role_name):
        # Retrieve its ARN
        iam_role_arn = get_iam_role_arn(role_name)
    else:
        iam_role_arn = create_iam_role_for_lambda(role_name)
        if iam_role_arn is None:
            # Error creating IAM role
            return None

    # Determine the Lambda runtime to use
    if ext == '.py':
        runtime = 'python3.7'
    elif ext == '.js':
        runtime = 'nodejs10.x'
    else:
        # Unexpected Lambda runtime
        return None

    # Deploy the Lambda function
    microservice = deploy_lambda_function(function_name, iam_role_arn,
                                          f'{filename}.{handler_name}',
                                          deployment_package,
                                          runtime,
                                          env_vars, region)
    if microservice is None:
        return None
    lambda_arn = microservice['FunctionArn']
    logging.info(f'Created Lambda function: {function_name}')
    logging.info(f'ARN: {lambda_arn}')
    return lambda_arn


def delete_lambda_function(function_name, iam_role_name, region):
    """Delete a Lambda function and its IAM role
    :param function_name: Lambda function to delete
    :param iam_role_name: IAM role associated with Lambda function
    :param region: Region containing the Lambda function
    :return: True if function was deleted, else False
    """

    # Delete all versions of the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        lambda_client.delete_function(FunctionName=function_name)
    except ClientError as e:
        logging.error(e)
        return False

    # Delete the IAM role associated with the function
    delete_iam_role(iam_role_name)
    return True


def invoke_lambda_function_synchronous(name, parameters, region):
    """Invoke a Lambda function synchronously
    :param name: Lambda function name or ARN or partial ARN
    :param parameters: Dict of parameters and values to pass to function
    :param region: Region containing the Lambda function
    :return: Dict of response parameters and values. If error, returns None.
    """

    # Convert the parameters from dict -> string -> bytes
    params_bytes = json.dumps(parameters).encode()

    # Invoke the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        response = lambda_client.invoke(FunctionName=name,
                                        InvocationType='RequestResponse',
                                        LogType='Tail',
                                        Payload=params_bytes)
    except ClientError as e:
        logging.error(e)
        return None
    return response


def get_lambda_arn(lambda_name, region):
    """Retrieve the ARN of a Lambda function
    :param lambda_name: Name of Lambda function
    :param region: Region containing the Lambda function
    :return: String ARN of Lambda function. If error, returns None.
    """

    # Retrieve information about the Lambda function
    lambda_client = boto3.client('lambda', region_name=region)
    try:
        response = lambda_client.get_function(FunctionName=lambda_name)
    except ClientError as e:
        logging.error(e)
        return None
    return response['Configuration']['FunctionArn']