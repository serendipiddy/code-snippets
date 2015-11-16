# from bs4 import BeautifulSoup as bs
import requests
from credentials import user_name, user_pass
import re, sys, json

# import boto3
# import botocore
import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from Email import send_message


# regex: http://stackoverflow.com/a/4667014
# regex no case: http://stackoverflow.com/a/500870
# regex reference: https://docs.python.org/2/library/re.html
# regex, re.S: http://stackoverflow.com/a/2199744
# time:  http://stackoverflow.com/a/2175170
# requests: http://docs.python-requests.org/en/latest/user/quickstart/
# sessions: http://docs.python-requests.org/en/latest/user/advanced/#session-objects
# referer: http://stackoverflow.com/a/20838143
# zip to dict: http://stackoverflow.com/a/209854
# elegant zipping to list: http://stackoverflow.com/a/8372442


S3_BUCKET = 'iddy-lambda-grades'

site_url = "https://my.vuw.ac.nz/cp/home/displaylogin";
login_url = "https://my.vuw.ac.nz/cp/home/login"
academic_record_url = "https://my.vuw.ac.nz/cp/ip/timeout?sys=sctssb&url=https://student-records.vuw.ac.nz/pls/webprod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu"
academic_record_ = "https://student-records.vuw.ac.nz/pls/webprod/bwsxacdh.P_FacStuInfo"
host = "https://my.vuw.ac.nz/"

URLmatch1 = '\/\*URL\*\/ "(.+)"'
pagetitle = '<title>(.+)</title>'

def try_match(match,text):
    """ Attempts to find match in text """
    try:
        m = re.search(match, text, re.IGNORECASE).group(1)
    except AttributeError:
        print( "not found, try again later" )
        sys.exit()
    return m
    
def parse_grades(html):
    """ Parses the student records HTML, returning the grades """

    # define regular expressions
    match_course = '([A-Z]{4}\d{3})'
    match_grade = '"dddefault">([A-Z][\+\-]?|&nbsp;)<'  # match grades, not term
    match_years = '<B>(\d{4})\d{2}</B>'
    match_table = '<TABLE .*?>(.*?)</TABLE>'  # group into tables for each year

    # filter webpage
    text = html.split('NAME="crse_hist">VUW Course History')[1]
    text = text.split('SUMMARY="This table displays the student Scholarship information."')[0]
    
    # match from html
    years = re.findall(match_years, text, re.S)
    table = re.findall(match_table, text, re.S)

    results = []

    i = 1
    while i < len(table):
        m_courses = re.findall(match_course,table[i],re.S)
        m_grades = re.findall(match_grade,table[i],re.S)
        
        # Use - to represent no grade
        j = 0
        while j < len(m_grades):
            if m_grades[j] == '&nbsp;':
                m_grades[j] = '-'
            j += 1
        results.append(zip(m_courses,m_grades))
        i+=2  # skip the title tables
    
    results = [list(a) for a in results]
    return dict(zip(years, results))
    
def get_student_records(session):
    """ Accesses student records from VUW """
    r_getrecords = session.get(academic_record_url, allow_redirects=True)
    
    if r_getrecords.status_code != 200:
        print('error, student records page not found (not status 200)')
        sys.exit()
    
    # SUPER IMPORTANT need to set where it came from..
    refer = 'https://student-records.vuw.ac.nz/pls/webprod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu'
    session.headers.update({'referer':refer})
    r_getrecords = session.get(academic_record_)
    
    print( "~~ %s" % try_match(pagetitle,r_getrecords.text))
      
    return r_getrecords
    
def update_grades(new, bucket):
    """ Overwrite the existing grade record with the new one """
    print ('~~ update grades')
    
    k = bucket.new_key('%s.json' % user_name)
    k.set_contents_from_string(json.dumps(new))
    k.generate_url(expires_in=300, force_http=True)
    
def check_grades(grades):
    """ Compare the new grades with existing record """
    conn = boto.connect_s3()
    bucket = conn.get_bucket(S3_BUCKET)
    key = bucket.get_key('%s.json' % user_name)
    
    # s3 = boto3.resource('s3')
    # key = s3.Object('mybucket', '%s.json' % user_name)
    
    # check it exists
    if not key:
        update_grades(grades, bucket)
        return True
    
    test_grades_old = key.get_contents_as_string()
    
    grades_data_existing = json.loads(test_grades_old)
    
    for y in grades_data_existing:
        if y not in grades:
            print('year %s not found, updating' % y)
            update_grades(grades, bucket)
            return True
        else:
            new = grades[y]
            old = grades_data_existing[y]
            
            for i in range(len(new)):
                if old[i][1] != new[i][1]:
                    print ('Grade change %s' % json.dumps(new[i]))
                    update_grades(new, bucket)
                    return True
    
    return False
    
def format_grades(grades):
    """ Formats the most recent grades nicely to view """
    # get most recent year
    max = 0;
    for y in grades:
        if int(y)>max: max = int(y)
    
    # make pretty
    out = 'Grades for %s:\n' % max
    for entry in grades[str(max)]:
        out = '%s%s %s\n' % (out, entry[0], entry[1])
        
    return out
    
def perform_duties():
    """ Run the main task """
    
    s = requests.Session()

    # Get page and extract UUID
    print( "~~ Getting login page" )
    r_loginpage = s.get(site_url)
    uuid = try_match('uuid.value="(.+)";',r_loginpage.text)

    # construct POST request, log in
    data = {'pass':user_pass, 'user':user_name, 'uuid':uuid}
    print( "~~ Attempting to login.." )
    r_loggingin = s.post(login_url, data=data, allow_redirects=True)
    print( "~~ %s" % try_match(pagetitle,r_loggingin.text))
    top_url = try_match(URLmatch1, r_loggingin.text)
    r_gethome = s.get(top_url, allow_redirects=True)

    if r_gethome.status_code != 200:
        print('error, homepage not found (not status 200)')
        sys.exit()

    # get and process academic records
    raw_html = get_student_records(s)
    grades = parse_grades(raw_html.text)

    # compare current grades
    if check_grades(grades):
        # format the recent year, and email
        print (format_grades(grades))
        send_message(format_grades(grades))
    else:
        print ('~~ No change to grades')
    
def lambda_handler(event, context):
    """ Call handler for AWS Lambda """
    
    perform_duties()
    
perform_duties()  # for offline