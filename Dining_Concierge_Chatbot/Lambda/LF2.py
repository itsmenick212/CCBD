def lambda_handler(event, context):
    import boto3;
    print("event is :" + str(event))
    sqs = boto3.client('sqs')

    queue_url = '<<Queue-url>>'

    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    print("Response is ============================" +str(response))
    if "Messages" in response.keys():
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        phoneNumber = message['MessageAttributes']['PhoneNumber']['StringValue']
        sns = boto3.client('sns')
        # Send a SMS message to the specified phone number
        response = sns.publish(
            PhoneNumber= phoneNumber,  # Get number from event
            Message='Here are your restaurant details. Bon Appetit!!'
        )
        # Delete received message from queue
        sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
        )
        print('Received and deleted message: %s' % message)




