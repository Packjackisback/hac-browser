from flask import request
import json
import os
import requests
from bs4 import BeautifulSoup

login_data = {
    '__RequestVerificationToken': '',
    'SCKTY00328510CustomEnabled': True,
    'SCKTY00436568CustomEnabled': True,
    'Database': 10,
    'VerificationOption': 'UsernamePassword',
    'LogOnDetails.UserName': '',
    'tempUN': '',
    'tempPW': '',
    'LogOnDetails.Password': ''
}

link = "https://homeaccess.katyisd.org/"




def getAssignments(login_data, link):
    with requests.Session() as ses:
        login_url = link + "HomeAccess/Account/LogOn"
        r = ses.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find(
            'input', attrs={'name': '__RequestVerificationToken'}
        )['value']

        # log in
        ses.post(login_url, data=login_data)

        r = ses.get(link + 'HomeAccess/Content/Student/Assignments.aspx')
        soup = BeautifulSoup(r.content, 'lxml')

        def get_val(name):
            el = soup.find("input", {"name": name})
            return el["value"] if el else ""

        payload = {
            "__EVENTTARGET": "ctl00$plnMain$btnRefreshView",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": get_val("__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": get_val("__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": get_val("__EVENTVALIDATION"),
            "ctl00$plnMain$ddlReportCardRuns": "ALL",
            "ctl00$plnMain$ddlClasses": "ALL",
            "ctl00$plnMain$ddlCompetencies": "ALL",
            "ctl00$plnMain$ddlOrderBy": "Class",
        }

        assignments = ses.post(
            link + 'HomeAccess/Content/Student/Assignments.aspx',
            data=payload
        )

        content = BeautifulSoup(assignments.text, 'lxml')

        classes = []
        averages = []
        finaldata = {"assignment": [], "categories": []}

        for class_group in content.find_all('div', class_='AssignmentClass'):
            header = class_group.find('div', class_="sg-header")
            if not header:
                continue
            class_name = header.find('a', class_='sg-header-heading').text.strip()[12:]
            avg_text = header.find('span', class_='sg-header-heading').text.strip()[18:]
            classes.append(class_name)
            averages.append(avg_text)

            tables = class_group.find_all('table', class_='sg-asp-table')
            if tables:
                assignmentstable = []
                for j in tables:
                    for row in j.find_all('tr'):
                        assignmentsrow = []
                        for td in row.find_all('td'):
                            text = td.get_text(strip=True).replace("*", "")
                            assignmentsrow.append(text)
                        if assignmentsrow:
                            assignmentstable.append(assignmentsrow)

                    if 'CourseCategories' in j.attrs['id']:
                        finaldata['categories'].append(assignmentstable)
                    elif 'CourseAssignments' in j.attrs['id']:
                        finaldata['assignment'].append(assignmentstable)

                    assignmentstable = []
            else:
                finaldata['assignment'].append([])
                finaldata['categories'].append([])

        ret = {}
        for i in range(len(classes)):
            assignments_for_class = finaldata['assignment'][i]
            if not assignments_for_class: 
                continue
            ret[classes[i]] = {
                "average": averages[i],
                "assignments": assignments_for_class,
                "categories": finaldata['categories'][i],
            }

        return ret if ret else None

def getWeighting(login_data,link):
    with requests.Session() as ses:
        login_url = link+"HomeAccess/Account/LogOn"
        r = ses.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = ses.post(login_url, data=login_data)
        classes = []
        averages = []

        finaldata = {}
        string = ''

        assignments = ses.get(link+'HomeAccess/Content/Student/Assignments.aspx')
        content = BeautifulSoup(assignments.text, 'lxml')

        for x in content.find_all('div', class_='AssignmentClass'):
            header = x.find('div', class_="sg-header")
            q = header.find('a', class_='sg-header-heading').text.strip()[12:]
            w = header.find('span', class_='sg-header-heading')
            classes.append(q.strip())
            averages.append(w.text.strip()[18:])

        string += ('\n\nClass Averages:\n')
        for i in range(len(classes)):
            string += ("\n" + classes[i] + " - " + averages[i])

        finaldata['classes'] = classes
        finaldata['averages'] = averages
        assignmentstable = []
        assignmentsrow = []

        finaldata['assignment'] = []
        finaldata['categories'] = []
        for x in content.find_all('div', class_='AssignmentClass'):
            table = x.find('table', class_='sg-asp-table')
            if table is not None:
                for j in x.find_all('table', class_='sg-asp-table'):
                    for row in j.find_all('tr'):
                        for element in row.find_all('td'):
                            text = element.text.strip()
                            text = text.replace("*", "")
                            assignmentsrow.append(text.strip())
                        assignmentstable.append(assignmentsrow)
                        assignmentsrow = []
                    if 'CourseCategories' in j.attrs['id']:
                        finaldata['categories'].append(assignmentstable)
                    elif 'CourseAssignments' in j.attrs['id']:
                        finaldata['assignment'].append(assignmentstable)
                    assignmentstable = []
            else:
                finaldata['assignment'].append([])
                finaldata['categories'].append([])
        ret = {}
        for i in range(len(classes)):
            average = averages[i]
            assig = finaldata['assignment'][i]
            categories = finaldata['categories'][i]
            l = {}
            l['average'] = average
            l['assignments'] = assig
            l['categories'] = categories
            ret[classes[i]] = l

        if len(ret) == 0:
            return None

        return ret

def getInfo(login_data, link):
    with requests.Session() as session:
        login_url = link+"HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        ret = {}
        assignments = session.get(link+'HomeAccess/Content/Student/Registration.aspx')
        content = BeautifulSoup(assignments.text, 'lxml')
        if content.find('span', id='plnMain_lblRegStudentName') is not None:
            ret['name'] = content.find('span', id='plnMain_lblRegStudentName').text.strip()
            ret['grade'] = content.find('span', id='plnMain_lblGrade').text.strip()
            ret['school'] = content.find('span', id='plnMain_lblBuildingName').text.strip()
            ret['dob'] = content.find('span', id='plnMain_lblBirthDate').text.strip()
            ret['councelor'] = content.find('span', id='plnMain_lblCounselor').text.strip()
            ret['language'] = content.find('span', id='plnMain_lblLanguage').text.strip()
            ret['cohort-year'] = content.find('span', id='plnMain_lblCohortYear').text.strip()
            return ret
        else:
            return None

def getAssignmentClass(login_data, class_name, link):
    with requests.Session() as ses:
        login_url = link+"HomeAccess/Account/LogOn"
        r = ses.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = ses.post(login_url, data=login_data)
        classes = []
        averages = []

        finaldata = {}
        string = ''

        assignments = ses.get(link+'HomeAccess/Content/Student/Assignments.aspx')
        content = BeautifulSoup(assignments.text, 'lxml')

        for x in content.find_all('div', class_='AssignmentClass'):
            if x.find('div', class_="sg-header") is None:
                return None
            header = x.find('div', class_="sg-header")
            q = header.find('a', class_='sg-header-heading').text.strip()[12:]
            w = header.find('span', class_='sg-header-heading')
            classes.append(q.strip())
            averages.append(w.text.strip()[18:])

        string += ('\n\nClass Averages:\n')
        for i in range(len(classes)):
            string += ("\n" + classes[i] + " - " + averages[i])

        finaldata['classes'] = classes
        finaldata['averages'] = averages
        assignmentstable = []
        assignmentsrow = []

        finaldata['assignment'] = []
        finaldata['categories'] = []
        for x in content.find_all('div', class_='AssignmentClass'):
            table = x.find('table', class_='sg-asp-table')
            if table is not None:
                for j in x.find_all('table', class_='sg-asp-table'):
                    for row in j.find_all('tr'):
                        for element in row.find_all('td'):
                            text = element.text.strip()
                            text = text.replace("*", "")
                            assignmentsrow.append(text.strip())
                        assignmentstable.append(assignmentsrow)
                        assignmentsrow = []
                    if 'CourseCategories' in j.attrs['id']:
                        finaldata['categories'].append(assignmentstable)
                    elif 'CourseAssignments' in j.attrs['id']:
                        finaldata['assignment'].append(assignmentstable)
                    assignmentstable = []
            else:
                finaldata['assignment'].append([])
                finaldata['categories'].append([])
        ret = {}
        for i in range(len(classes)):
            if(classes[i] == class_name):
                average = averages[i]
                assig = finaldata['assignment'][i]
                categories = finaldata['categories'][i]
                l = {}
                l['average'] = average
                l['assignments'] = assig
                l['categories'] = categories
                ret[classes[i]] = l
                return ret

        return json.dumps({"error":"class not found"}), 404, {'ContentType':'application/json'}

def getAverages(login_data, link):
    with requests.Session() as session:
        login_url = link+"HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        classes = []
        averages = []
        assignments = session.get(link+'HomeAccess/Content/Student/Assignments.aspx')
        content = BeautifulSoup(assignments.text, 'lxml')

        for x in content.find_all('div', class_='AssignmentClass'):

            header = x.find('div', class_="sg-header")
            q = header.find('a', class_='sg-header-heading').text.strip()[12:]
            w = header.find('span', class_='sg-header-heading')
            classes.append(q.strip())
            averages.append(w.text.strip()[18:])

        ret = {}
        for i in range(len(classes)):
            ret[classes[i]] = averages[i]

        if len(ret) == 0:
            return None

        return ret

def getClasses(login_data, link):
    with requests.Session() as session:
        login_url = link+"HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        classes = []
        assignments = session.get(link+'HomeAccess/Content/Student/Assignments.aspx')
        content = BeautifulSoup(assignments.text, 'lxml')

        for x in content.find_all('div', class_='AssignmentClass'):

            header = x.find('div', class_="sg-header")
            q = header.find('a', class_='sg-header-heading').text.strip()[12:]
            classes.append(q.strip())

        ret = {}
        ret['classes'] = classes
        return ret

def getReport(login_data, link):
    with requests.Session() as session:
        login_url = link + "HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        finaldata = {}
        reportcard = session.get(link+'HomeAccess/Content/Student/ReportCards.aspx')
        reportcardcontent = BeautifulSoup(reportcard.text, 'lxml')
        headers = ['Course', 'Description', 'Period', 'Teacher', 'Room', '1st', '2nd', '3rd', 'Exam1', 'Sem1', '4th', '5th', '6th', 'Exam2', 'Sem2', 'CND1', 'CND2', 'CND3', 'CND4', 'CND5', 'CND6']
        row = []
        data = []
        finaldata['headers'] = headers
        counter = 0
        for x in reportcardcontent.find_all('td'):
            counter += 1
            # if counter <= 32:
            #     headers.append(x.text.strip())
            if counter > 32:
                row.append(x.text.strip())
            if (len(row) % 32 == 0) and (counter > 32):
                data.append(row)
                row = []
        for j in data:
            del j[31]
            del j[30]
            del j[29]
            del j[28]
            del j[27]
            del j[26]
            del j[25]
            del j[24]
            del j[23]
            del j[6]
            del j[5]
        finaldata['data'] = data
        if len(finaldata['data']) == 0:
            return None
        return finaldata

def getProgressReport(login_data, link):
    with requests.Session() as session:
        login_url = link+"HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        finaldata = {}
        string = ''
        reportcard = session.get(link+'HomeAccess/Content/Student/InterimProgress.aspx')
        reportcardcontent = BeautifulSoup(reportcard.text, 'lxml')

        headers = []
        row = []
        data = []
        if reportcardcontent.find_all('tr') is None:
            return None
        for x in reportcardcontent.find_all('tr'):
            for c in x.find_all('td'):
                row.append(c.text.strip())
            data.append(row)
            row = []

        if len(data)==0:
            return None
        headers = data[0]
        data.pop(0)
        finaldata['headers'] = headers
        finaldata['data'] = data
        return finaldata

def getName(login_data, link="https://homeaccess.katyisd.org/"):
    with requests.Session() as ses:
        data = {}
        login_url = link + "HomeAccess/Account/LogOn"
        r = ses.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = ses.post(login_url, data=login_data)
        page = ses.get(link + 'HomeAccess/Home/WeekView')
        content = BeautifulSoup(page.text, 'lxml')
        if content.find('div', class_='sg-banner-menu-container') is None:
            return None
        container = content.find('div', class_='sg-banner-menu-container')
        name = container.find('span')
        return name.text.strip()

def getTranscript(login_data, link):
    with requests.Session() as session:
        login_url = link + "HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        finaldata = []
        year = []
        semester = []
        transcript = session.get(link+ "HomeAccess/Content/Student/Transcript.aspx")
        content = BeautifulSoup(transcript.text, 'lxml')
        transcript = {}

        if content.find_all('td', class_='sg-transcript-group') is None:
            return None

        for x in content.find_all('td', class_='sg-transcript-group'):
            semester = {}
            table1 = x.find_next('table')
            table2 = table1.find_next('table')
            table3 = table2.find_next('table')
            for y in table1.find_all('span'):
                if "YearValue" in y.attrs['id']:
                    semester['year'] = y.text.strip()
                if "GroupValue" in y.attrs['id']:
                    semester['semester'] = y.text.strip()
                if "GradeValue" in y.attrs['id']:
                    semester['grade'] = y.text.strip()
                if "BuildingValue" in y.attrs['id']:
                    semester['school'] = y.text.strip()
            data = []
            semester['data'] = []
            for z in table2.find_all('tr'):
                if "sg-asp-table-header-row" in z.attrs['class']:
                    for a in z.find_all('td'):
                        data.append(a.text.strip())
                    semester['data'].append(data)
                    data = []
                if "sg-asp-table-data-row" in z.attrs['class']:
                    for a in z.find_all('td'):
                        data.append(a.text.strip())
                    semester['data'].append(data)
                    data = []
            for z in table3.find_all('label'):
                if "CreditValue" in z.attrs['id']:
                    semester['credits'] = z.text.strip()
            transcript[semester['year'] + " - Semester "+ semester['semester']] = semester
        x = content.find('table', id='plnMain_rpTranscriptGroup_tblCumGPAInfo')

        if x is None:
            return None

        for y in x.find_all('tr', class_="sg-asp-table-data-row"):
            for z in y.find_all('span'):
                if "GPADescr" in z.attrs['id']:
                    num = z.find_next('span')
                    text = z.text.strip()
                    transcript[text] = num.text.strip()

        transcript['Rank'] = content.find('span', id='plnMain_rpTranscriptGroup_lblGPARank3').text.strip()
        return transcript

def getRank(login_data, link):
    with requests.Session() as session:
        login_url = link + "HomeAccess/Account/LogOn"
        r = session.get(login_url)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        post = session.post(login_url, data=login_data)
        finaldata = []
        year = []
        semester = []
        transcript = session.get(link+ "HomeAccess/Content/Student/Transcript.aspx")
        content = BeautifulSoup(transcript.text, 'lxml')
        rank = (content.find('span', id='plnMain_rpTranscriptGroup_lblGPARank3').text.strip())
        return rank

def checkLink(link):
    # try:
    with requests.Session() as session:
        login_url = link + "HomeAccess/Account/LogOn"
        try:
            r = session.get(login_url)
        except:
            return False
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['__RequestVerificationToken'] = soup.find('input', attrs={'name': '__RequestVerificationToken'})['value']
        return True

def classes():
    if 'user' in request.args and 'pass' in request.args :
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getClasses(data, link)
        if len(content['classes']) == 0:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}

        return json.dumps(content), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def ipr():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getProgressReport(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}
        return json.dumps(content), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def reportcard():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getReport(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}
        return json.dumps(content), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def averages():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getAverages(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}
        return json.dumps(content), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def assignments(user, password):
    if user and password:
        link = "https://homeaccess.katyisd.org/"
        data = login_data
        data['LogOnDetails.UserName'] = user
        data['LogOnDetails.Password'] = password
        content = getAssignments(data, link)
        return json.dumps(content)
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def info():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getInfo(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}

        return json.dumps(content), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def transcript():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getTranscript(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}
        return json.dumps(content), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def name():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getName(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}
        return json.dumps({'name':content}), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

def rank():
    if 'user' in request.args and 'pass' in request.args:
        link = "https://homeaccess.katyisd.org/"
        if 'link' in request.args:
            link = request.args['link']
            if link[-1] != '/':
                link += '/'
            if link[:8] != 'https://':
                link = 'https://' + link
            if not checkLink(link):
                return json.dumps({'success': False, 'message': 'Invalid link'}), 200, {"Content-Type": "application/json"}
        data = login_data
        data['LogOnDetails.UserName'] = request.args['user']
        data['LogOnDetails.Password'] = request.args['pass']
        content = getRank(data, link)
        if content is None:
            return json.dumps({'success': False, 'message': 'Invalid username or password'}), 200, {"Content-Type": "application/json"}
        return json.dumps({'rank':content}), 200, {"Content-Type": "application/json"}
    return json.dumps({'success': False, 'message': 'Missing required headers: link, user and pass', 'documentation':'https://homeaccesscenterapi-docs.vercel.app/'}), 406, {"Content-Type": "application/json"}

