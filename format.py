from bs4 import BeautifulSoup
from string import Template
from itertools import groupby
import os
import re
import locale
import time
import argparse
import sys
from datetime import timedelta,datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

jinjaloader=FileSystemLoader(
    os.path.dirname(os.path.abspath(__file__)) + '/templates')
jinjaenv = Environment(
    loader=jinjaloader,
#    autoescape=select_autoescape(['html', 'xml'])
)


exclude_cates = set(
"""Minimes et Femmes MC
Cadets et Femmes JS
UCI Juniors
Cadets
Ecole de route
Ecoles de cyclisme
Elite Nationale
Autres
UCI classe 2
1-2
Minimes
Juniors
Femmes MC
Handisport
Fédérale Juniors
Régionale Juniors
Randonnée VTT""".splitlines())

exclude_types = set(
"""Randonnée
AG
VTT
Bourse""".splitlines())

# for parsing dates
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


## DOWNLOAD FUNCTIONS

def get_ffc(fichier):
    html = open(fichier,'r',encoding='utf8')
    soup = BeautifulSoup(html, 'html5lib')
    courses_table = soup.find(attrs={'class':'se_mod_allevents_contenu'}).table

    courses = []
    for c in courses_table.tbody.contents[::2]:
        details = c.next_sibling.td.contents
        c_el = {
            'fede':'FFC',
            'nom':re.sub(r'^.*?- +','',c.get_text()).title(),
            'date':time.strptime(details[0].get_text(),'%A %d %B %Y'),
            'cate':details[3].get_text(),
            'lieu':details[6].get_text(),
            'lien':'http://www.auvergnerhonealpescyclisme.com' + details[7]['href'],
        }
        courses.append(c_el)
    return courses

def get_fsgt69():
    html = open('cal69.html','r',encoding='utf8')
    soup = BeautifulSoup(html, 'html.parser')
    courses_table = soup.find(attrs={'class':'table-striped'})

    courses = []
    for c in courses_table.find_all(attrs={'class':'epreuve'}):
        cc = c.find_all('td')
        # print(cc)
        c_el = {
            'fede':'FSGT 69',
            'nom':cc[2].get_text(),
            'date':time.strptime(cc[0].get_text(),'%d/%m/%Y'),
            'cate':'',
            'lieu':'',
            'type':cc[1].get_text(),
            'lien': 'http://www.cyclismerhonefsgt.fr' + cc[2].a['href'] if cc[2].a else '',
        }
        courses.append(c_el)
    return courses

def get_fsgt42():
    html = open('cal42.html','r',encoding='utf8')
    soup = BeautifulSoup(html, 'html.parser')
    courses_table = soup.find_all('table')[1]

    courses = []
    for c in courses_table.find_all('tr')[1:]:
        # print(c)  
        c_el = {
            'fede':'FSGT 42',
            'nom':c.contents[3].get_text().strip(),
            'date':time.strptime(c.contents[1].get_text().strip(),'%d/%m/%Y'),
            'cate':'',
            'lieu':'',
            'lien': 'http://www.fsgt42.com' + c.contents[3].a['href'],
        }
        courses.append(c_el)
    return courses

def get_fsgt71():
    html = open('cal71.html','r',encoding='utf8')
    soup = BeautifulSoup(html, 'html5lib')
    courses_table = soup.find(attrs={'id':'tableau'})

    courses = []
    month = ''
    # print(courses_table)
    for c in courses_table.contents:
        if c.name == 'thead':
            month = c.tr.th.get_text()[-3:]
            # print(c.tr.th.get_text())
        elif c.name == 'tbody':
            ctrs = c.find_all(attrs={'class':'annonce-course'})

            for ctr in ctrs:
                ctrtd = ctr.find_all('td')
                if len(ctrtd)<3 or len(re.findall(r'[0-3]?[0-9]',ctrtd[0].get_text()))==0:
                    if not 'COLE' in (ctr.get_text()): # ECOLE DE VELO
                        print('ERROR IMPORTING:', ctrtd,file=sys.stderr)
                else:
                    dayofmonth = re.findall(r'[0-3]?[0-9]',ctrtd[0].get_text())[0]
                    # print(ctrtd[0].get_text())
                    c_el = {
                        'fede':'FSGT 71',
                        'nom': ctrtd[1].get_text().title(),
                        'date': time.strptime(dayofmonth+ ' ' + month + ' 2018','%d %m %Y'),
                        'cate': '',
                        'lieu': ctrtd[3].get_text(),
                        'lien': 'http://www.fsgt71velo.fr/2018/calendrier/' + ctrtd[1].a['href'] if ctrtd[1].a else '',
                    }
                    courses.append(c_el)
    return courses


## FORMATING FUNCTIONS


def cate_key(c):
    if c['fede'] == 'FSGT 69': return 1
    if c['fede'] == 'FSGT 71': return 2
    if c['fede'] == 'FSGT 42': return 3
    if 'Open' in c['cate']: return 5
    else: return 4

sttodt = lambda x:datetime.fromtimestamp(time.mktime(x))

def getsamediorday(x):
    dt = datetime.fromtimestamp(time.mktime(x))
    ret = dt+timedelta(days=5-dt.weekday()) if dt.weekday() in [4,5,6] else dt+timedelta(days=-2) if dt.weekday()==0 else dt
    return ret.timetuple()

def format_forum(courses,filter=False):
    kf = lambda x:x['date']
    kf2 = lambda x:getsamediorday(x[0]['date'])

    courses = courses
    try:
        folder_date = datetime.strptime(args.folder,'%Y-%m-%d')
        courses = [c for c in courses if datetime.fromtimestamp(time.mktime(c['date']))>folder_date]
    except ValueError:
        pass

    if filter:
        courses = [c for c in courses if c['date']>time.gmtime() and datetime.fromtimestamp(time.mktime(c['date']))<datetime.now()+timedelta(days=10)]
    else:
        courses = [c for c in courses if c['date']>time.gmtime()]

    courses = sorted(courses,key=cate_key)
    courses = sorted(courses, key=kf)

    byd = [list(v) for k,v in groupby(courses,kf)]
    # print(byd)
    bywe = [list(v) for k,v in groupby(byd,kf2)]
    return bywe


## PROGRAM START

parser = argparse.ArgumentParser()
parser.add_argument('folder',nargs='?',default='.')
parser.add_argument('-f',choices=['forum','html','txt'],default='forum')
parser.add_argument('--noopen',action='store_true',help='Exclure les courses accessibles uniquement avec licence PCO')

args = parser.parse_args()

os.chdir(args.folder)

# courses = get_ffc()
courses = get_fsgt42() + get_ffc('calffc.html') + get_ffc('calffcl.html') + get_fsgt69() + get_fsgt71()
courses = [el for el in courses if
    not el['cate'] in exclude_cates and
    (not 'type' in el or not el['type'] in exclude_types) and
    (not "Pass'Open" in el['cate'] or not args.noopen) and
    (not 'Rando' in el['nom']) and
    (not 'RANDO' in el['nom']) and
    (not 'BREVET' in el['nom'])
    ]

for el in courses:
    el['fede_slug']=re.sub(' ','-',el['fede']).lower()
    el['cate_slug']=re.sub("[ ']",'-',el['cate']).lower()
    el['lieu']=el['lieu'].title()


jinjaenv.filters['datef'] = lambda d:time.strftime('%a %d %B',d).capitalize()
jinjaenv.filters['day'] = lambda d:time.strftime('%a %d',d).capitalize()

def formatwe(d):
    dt = sttodt(d)
    if dt.weekday() in [4,5,6,0]:
        return time.strftime('WE du %d %B',d)
    else:
        return time.strftime('%a %d %B',d)

jinjaenv.filters['formatwe'] = formatwe


if args.f == 'forum':
    data = format_forum(
        courses,
        filter=True)
    print(jinjaenv.get_template("forum.txt").render(data=data))
elif args.f == 'txt' :
    data = format_forum(
        courses,
        filter=False)
    print(jinjaenv.get_template("txt.txt").render(data=data))
elif args.f == 'html' :
    data = format_forum(
        courses,
        filter=False)
    print(jinjaenv.get_template("html.html").render(data=data))

#    TODO :
#    - écrire la doc