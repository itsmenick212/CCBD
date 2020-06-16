import boto3
client = boto3.client('apigateway')

response = client.put_integration(
    restApiId='oz0udayqt2',
    resourceId='yjka0cb358',
    httpMethod='POST',
    type='AWS',
    integrationHttpMethod='POST',
    uri='arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:097032291048:function:LF0/invocations',
    timeoutInMillis=123
)