# Description

Lambda function to query student records for new exam results. Uses Amazon SES to email when new results are released.

## Setup

### Amazon
#### S3 bucket
    create bucket (default access)
    set name of bucket on line 27 pygrades.py
#### SES
    verify the email address(s) you want to send from AND to
#### lambda
    set role to read/write to S3 and SES
    event source: scheduled (hourly? daily?)

### Function
#### setting credentials
    credentials_template.py > credentials.py
  
#### load on EC2
    $ cd function_dir
    bundle up with modules
      $ pip intall requests -t .
      $ pip intall boto -t .
      $ zip -r data *
    upload that file to lambda console
    
#### test it works
     on lambda page 'test'
     should return null and '~~ update grades' in S3 folder
     an email should then arrive at the configured address
     
     To test emailing, delete the file in S3 and test again or wait for scheduled send
