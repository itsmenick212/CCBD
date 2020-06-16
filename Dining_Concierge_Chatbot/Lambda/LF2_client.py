import Lambda.LF2.lambda_util
import Lambda.LF2.LF2
import boto3

from Lambda.LF2 import lambda_util

client = boto3.client('lambda')
events_client = boto3.client('events')
policies = ['arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole',
            'arn:aws:iam::aws:policy/AmazonSNSFullAccess']
lambda_util.create_iam_role_for_lambda("lambda_sqs",policies)
lambda_arn =lambda_util.create_lambda_function("Queue_Processor", "LF2.py", "lambda_handler", "lambda_sqs",
                           "us-east-1", env_vars={})

response = client.add_permission(
    FunctionName="Queue_Processor",
    StatementId='SQSPermission',
    Action='lambda:InvokeFunction',
    Principal = "395460460730",                               # Account id to whom queue belongs
    SourceArn = "arn:aws:sqs:us-east-1:395460460730:Queue1")  #Queue arn

# response = client.create_event_source_mapping(
#     EventSourceArn='arn:aws:sqs:us-east-1:395460460730:Queue1',      #Queue arn
#     FunctionName='Queue_Processor',
#     Enabled=True,
#     BatchSize=10
#    )
frequency = "rate(1 minute)"
name = "{0}-Trigger".format('Queue_Processor')
rule_response = events_client.put_rule(
    Name=name,
    ScheduleExpression=frequency,
    State='ENABLED',
)
client.add_permission(
    FunctionName='Queue_Processor',
    StatementId="{0}-Event".format(name),
    Action='lambda:InvokeFunction',
    Principal='events.amazonaws.com',
    SourceArn=rule_response['RuleArn'],
)
events_client.put_targets(
    Rule=name,
    Targets=[
        {
            'Id': "1",
            'Arn': lambda_arn,
        },
    ]
)