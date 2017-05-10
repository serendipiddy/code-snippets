## Python AWS Lambda function to start an EC2 instance given a 6-digit OTP for authentication 
## OTP secret must be generated manually and placed as a tag on the instance you wish start this way
##    tag name for secret is tag_dict['secret'], defined below

import boto3
import pyotp

tag_dict = {
    "secret" : "auth_secret",
    # "attempts" : "attempts",
    # "time" : "last_attempt_time"
}

from datetime import datetime

event_instance = 'instance-keyword'
event_otp = 'otp-keyword'

domain = 'lambda.b.c'
email_dest = "a@b.c"
email_src = "lambda@b.c"

ec2_state_stopped = 80  # status code for EC2's 'stopped' state 
# attempts_per_minute_limit = 3  # limits attempts to 3 each minute.  # TODO -- but cloudfront can rate limit 

def get_existing_ec2_instances():
    ''' Retrieve the existing ec2 instances for this account '''
    
    client = boto3.client('ec2')
    descriptions = client.describe_instances( InstanceIds=[] )
    
    print( "Number of reservations: {}".format(len(descriptions['Reservations'])) )
    instances_desc = descriptions['Reservations'][0]['Instances']  # assumes a single/the first reservation...?
    
    return [d['InstanceId'] for d in instances_desc]

def get_instance_secret( ec2_instance ):
    ''' Returns the secret associated with this instance, or None if not found '''
    
    gen = (x for x in ec2_instance.tags if x['Key'] == tag_dict['secret'])
    value = None
    
    try:
        value = gen.next()
    except StopIteration:
        return None
    
    return value['Value']

def generate_email(sender, destination, subject, message):
    ''' Creates an email for sending with SES '''
    
    email = dict()
    email['Source'] = sender
    email['Destination'] = {'ToAddresses' : [destination]}
    email_subject = {
        'Charset':'UTF-8',
        'Data':subject
    }
    email_body = { 
        'Html': {
            'Charset':'UTF-8', 
            'Data':"<html><body><p>{}</p></body></html>".format(message.replace("\n","</p></br><p>"))
        }, 
        'Text': { 
            'Charset':'UTF-8', 
            'Data':message 
        }
    }
    email['Message'] = {
        'Subject': email_subject, 
        'Body': email_body
    }
    
    return email

def send_status_email( subject, message ):
    ''' Notifies, via email, the result of the latest attempt. '''
    
    the_date = "UTC: {}".format(datetime.utcnow())
    
    subject = "AWS Lambda notification - {}".format(subject)
    message = "Lambda Function {}\n{}\n{}".format(domain, the_date, message)
    
    email = generate_email(email_src, email_dest, subject, message)
    
    ses = boto3.client("ses")
    ses.send_email(Source=email['Source'], Destination=email['Destination'], Message=email['Message'])

def lambda_handler(event, context):
    
    event = json.loads(event['body'])
    
    if event_instance not in event or event_otp not in event:
        subject = "EC2 Start Failed"
        message = 'Incorrectly formatted lambda event'
        send_status_email(subject, message)
        return 'Incorrectly formatted lambda event'
    
    instance_id = event[event_instance]
    submitted_otp = event[event_otp]
    
    print( "id:{} otp:{}".format(instance_id, submitted_otp) )
    
    existing_instances = get_existing_ec2_instances()
    if instance_id not in existing_instances:
        subject = "EC2 Start Failed"
        message = 'Instance "{}" does not exist'.format(instance_id)
        send_status_email(subject, message)
        return 'Instance "{}" does not exist'.format(instance_id)
    
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance( instance_id )
    the_secret = get_instance_secret( instance )
    
    totp = pyotp.TOTP( the_secret )
    if totp.verify( submitted_otp ) and instance.state['Code'] == ec2_state_stopped:
        instance.start()
        subject = "EC2 Start Success"
        message = 'Successfully started ECS instance'
        send_status_email(subject, message)
    else:
        subject = "EC2 Start Failed"
        message = 'Incorrect OTP given {}'.format(submitted_otp)
        send_status_email(subject, message)
        print('OTP verify failed')
    
    return 'Completed lambda EC2/OTP function'
