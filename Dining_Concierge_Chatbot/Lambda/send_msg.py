
'''
sample sns code
'''
import boto3
sns = boto3.client('sns')

# Send a SMS message to the specified phone number
response = sns.publish(
    PhoneNumber='+19293859381',
    Message='Hello World!',
)

# Print out the response
print(response)