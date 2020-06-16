import boto3
client = boto3.client('apigateway')

response = client.create_rest_api(
    name='dining_concierge_API',
    description='Dining Concierge API',
    version='1',
    minimumCompressionSize=123,
    apiKeySource='HEADER'
)


