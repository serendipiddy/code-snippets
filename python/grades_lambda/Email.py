import boto3
from credentials import email_from, email_to


def send_message(message):
    # SERVER = "localhost"

    FROM = email_from
    TO = [email_to] # must be a list
    SUBJECT = "New Grades"

    client = boto3.client('ses')
    response = client.send_email(
        Source=FROM,
        Destination={
            'ToAddresses': TO,
            'CcAddresses': [],
            'BccAddresses': []
        },
        Message={
            'Subject': {
                'Data': SUBJECT
            },
            'Body': {
                'Text': {
                    'Data': message
                }
            }
        }
    )
    
    return response