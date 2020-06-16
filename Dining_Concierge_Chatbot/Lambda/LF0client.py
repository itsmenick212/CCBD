import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    # TODO implement
    message = event['name']
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='DiningConcierge',
        botAlias='Promod',
        userId='John',
        inputText=message
    )

    logger.debug(response)
    return {'message': response['message']}

