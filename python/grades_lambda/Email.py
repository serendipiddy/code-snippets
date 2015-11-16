import smtplib

# adapted from: http://stackoverflow.com/a/24271220

def send_message(message):
    SERVER = "localhost"

    FROM = "clouddy@ec2"
    TO = ["serendipiddy@gmail.com"] # must be a list
    SUBJECT = "New Grades"

    # Prepare actual message
    message = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (FROM, ", ".join(TO), SUBJECT, message)

    # Send the mail
    server = smtplib.SMTP(SERVER)
    server.sendmail(FROM, TO, message)
    server.quit()