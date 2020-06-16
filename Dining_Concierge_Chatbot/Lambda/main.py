import boto3
import json
import yaml

def setup_roles():
    """ Sets up AWS IAM roles for executing this lambda function. """

    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html
    # https://docs.aws.amazon.com/lambda/latest/dg/policy-templates.html
    # https://docs.aws.amazon.com/lambda/latest/dg/intro-permission-model.html#lambda-intro-execution-role

    basic_role = """
    Version: '2012-10-17'
    Statement:
        - Effect: Allow
          Principal: 
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    """

    iam = boto3.client('iam')

    # lambda.awazonaws.com can assume this role.
    iam.create_role(RoleName=config['role'],
                    AssumeRolePolicyDocument=json.dumps(yaml.full_load(basic_role)))

    # This role has the AWSLambdaBasicExecutionRole managed policy.
    iam.attach_role_policy(RoleName=config['role'],
                           PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')


def get_logs():
    """ Returns all logs related to the invocations of this lambda function. """
    log = boto3.client('logs')
    groupName = '/aws/lambda/' + config['name']
    return log.filter_log_events(logGroupName=groupName)


def create_function():
    """ Creates and uploads the lambda function. """

    lam = boto3.client('lambda')
    iam = boto3.client('iam')

    # Creates a zip file containing our handler code.
    import zipfile
    with zipfile.ZipFile(config['zip'], 'w') as z:
        z.write(config['path'])

    # Loads the zip file as binary code.
    with open(config['zip'], 'rb') as f:
        code = f.read()

    role = iam.get_role(RoleName=config['role'])
    return lam.create_function(
        FunctionName=config['name'],
        Runtime='python3.6',
        Role=role['Role']['Arn'],
        Handler=config['handler'],
        Code={'ZipFile': code})


def update_function():
    """ Updates the function. """

    lam = boto3.client('lambda')

    # Creates a zip file containing our handler code.
    import zipfile
    with zipfile.ZipFile(config['zip'], 'w') as z:
        z.write(config['path'])

    # Loads the zip file as binary code.
    with open(config['zip'], 'rb') as f:
        code = f.read()

    return lam.update_function_code(
        FunctionName=config['name'],
        ZipFile=code)


def invoke_function(first, last):
    """ Invokes the function. """

    lam = boto3.client('lambda')
    resp = lam.invoke(
        FunctionName=config['name'],
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps({'first_name': first, 'last_name': last}))

    print(resp['Payload'].read())
    return resp


# setup_roles()
# get_logs()
# create_function()
with open('./configLF1.yaml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
# update_function()
get_logs()
