# from bs4 import BeautifulSoup as bs
import requests
from credentials import user_name, user_pass
import re, sys, json
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


site_url = "https://my.vuw.ac.nz/cp/home/displaylogin";
login_url = "https://my.vuw.ac.nz/cp/home/login"
academic_record_url = "https://my.vuw.ac.nz/cp/ip/timeout?sys=sctssb&url=https://student-records.vuw.ac.nz/pls/webprod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu"
academic_record_ = "https://student-records.vuw.ac.nz/pls/webprod/bwsxacdh.P_FacStuInfo"
host = "https://my.vuw.ac.nz/"

user_name = ''
user_pass = ''

URLmatch1 = '\/\*URL\*\/ "(.+)"'
URLmatch2 = '\/\*URL\*\/ \'(.+)\''
pagetitle = '<title>(.+)</title>'
matchStudy = 'href=\"(.+)\">My Study'
matchAcademic = 'href=\"(.+)" title="">Academic'

def try_match(match,text):
    try:
        m = re.search(match, text, re.IGNORECASE).group(1)
    except AttributeError:
        print( "not found, try again later" )
        sys.exit()
    return m
    
def print_cookies(cookies):
    i = 0
    for c in cookies:
        print("%d %s\n    %s %s" % (i, c.name, c.value, c.domain))
        i += 1
        
def parse_grades(html):
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
    
def get_student_records(s):
    # print(s.cookies)
    # print('\n')
    
    r_getrecords = s.get(academic_record_url, allow_redirects=True)
    # print(r_getrecords.headers)
    # print(r_getrecords.url)
    # print(r_getrecords.text)
    # print_cookies(r_getrecords.cookies)
    # print_cookies(s.cookies)
    # print('\n')
    
    # SUPER IMPORTANT need to set where it came from..
    refer = 'https://student-records.vuw.ac.nz/pls/webprod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu'
    # s.cookies.clear('my.vuw.ac.nz','/','JSESSIONID')  # didn't help
    s.headers.update({'referer':refer})
    r_getrecords = s.get(academic_record_)
    # print(r_getrecords.headers)
    # print(r_getrecords.url)
    # print_cookies(s.cookies)
    
    print( "~~ %s" % try_match(pagetitle,r_getrecords.text))
      
    # print(r_getrecords.text)
    return r_getrecords
    
def get_through_myvuw(s):
    study_url = try_match(matchStudy,r_gethome.text)
    r_study = s.get(host+academic_record_3, allow_redirects=True)
    print(r_study.text)
    # study_url = try_match(matchAcademic,r_study.text)
    # print(r_study.url)
    
s = requests.Session()

# Get page and extract UUID for cookie
print( "~~ Getting login page" )
r_loginpage = s.get(site_url)
# print_cookies(r_loginpage.cookies)
uuid = try_match('uuid.value="(.+)";',r_loginpage.text)

# print('~~ UUID is %s' % uuid)

# construct POST request
data = {'pass':user_pass, 'user':user_name, 'uuid':uuid}
print( "~~ Attempting to login.." )
r_loggingin = s.post(login_url, data=data, allow_redirects=True)
print( "~~ %s" % try_match(pagetitle,r_loggingin.text))
top_url = try_match(URLmatch1, r_loggingin.text)
r_gethome = s.get(top_url, allow_redirects=True)

# print(top_url)

# print(r_gethome.text)
# print_cookies(s.cookies)
# r_gethome = s.get(site_url, allow_redirects=True)

# print('\n')
raw_html = get_student_records(s)
grades = parse_grades(raw_html.text)

for y in grades:
    print("%s: %s" % (y,grades[y]))

send_message('hello')