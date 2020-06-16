import json
import boto3

def lambda_handler(event, context):
    lex = boto3.client('lex-runtime')
    response = lex.post_text(
    botName='searchImage',
    botAlias="searchImageBot",
    userId="nick_guota",
    inputText="Show me a giraffe anf a toger"
    )
    return "Hi, how can I help you today?"
