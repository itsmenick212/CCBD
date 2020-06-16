import json
import boto3
import time
import requests

API_ENDPOINT = "https://vpc-photos-syjqysac4x5asu6rpjuinxvsjq.us-east-1.es.amazonaws.com/photos/0"

def lambda_handler(event, context):
    jsonBody = event['Records'][0]
    bucketName =  jsonBody['s3']['bucket']['name']
    key = jsonBody['s3']['object']['key']
    reko=boto3.client('rekognition')
    try:
        data = {}
        response = reko.detect_labels(Image={'S3Object':{'Bucket':bucketName,'Name':key}})
        data['objectKey'] = key
        data['bucket'] = bucketName
        data['createdTimestamp'] = time.time()
        data['labels'] = []
        for label in response['Labels']:
            print (label['Name'] + ' : ' + str(label['Confidence']))
            data['labels'].append(label['Name'])
        json_data = json.dumps(data)
        headers = { "Content-Type": "application/json" }
        r = requests.post(url = API_ENDPOINT, data = json_data, headers = headers)
    except Exception as e:
        print("Error "+ str(e))
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Nick Gupta's Lambda function!')
    }
