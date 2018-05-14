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
Femmes MC
Handisport
Fédérale Juniors
Régionale Juniors""".splitlines())

exclude_types = set(
"""Randonnée
AG
VTT
Bourse""".splitlines())

# for parsing dates
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


## DOWNLOAD FUNCTIONS

def get_ffc():
    html = open('calffc.html','r',encoding='utf8')
    soup = BeautifulSoup(html, 'html.parser')
    courses_table = soup.find(attrs={'id':'se_mod_allevents_171'}).table

    courses = []
    for c in courses_table.contents[::2]:
        details = c.next_sibling.td.contents
        c_el = {
            'fede':'FFC',
            'nom':re.sub(r'^.*?- +','',c.get_text()),
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
                        'nom': ctrtd[1].get_text(),
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

def format_forum(courses,tmpl,dateTmpl=Template('$date : \n'),filter=False):
    kf = lambda x:x['date']
    if filter:
        courses = [c for c in courses if c['date']>time.gmtime() and datetime.fromtimestamp(time.mktime(c['date']))<datetime.now()+timedelta(days=10)]
    courses = sorted(courses, key=kf)
    out = ''
    for k, gg in groupby(courses, kf):
        # out+= time.strftime('%a %d %B',k) + ' :\n'
        out += dateTmpl.substitute({"date":time.strftime('%a %d %B',k)})
        g = sorted(gg, key=cate_key)
        for c in g:
            c['datef'] = time.strftime('%a %d %B',c['date'])
            out += tmpl.substitute(c)
    return out


raw_template = Template('\t$fede $cate\t$nom\t$lieu\n')
forum_template = Template('- $fede $cate : [url=$lien]$nom[/url] $lieu\n')
html_template = Template("""<tr class='course'>
    <td>$fede $cate</td>
    <td><a href='$lien'>$nom</a></td><td>$lieu</td>
</tr>\n""")

## PROGRAM START

parser = argparse.ArgumentParser()
parser.add_argument('folder',nargs='?',default='.')
parser.add_argument('-f',choices=['forum','html','txt'],default='forum')

args = parser.parse_args()

os.chdir(args.folder)

# courses = get_ffc()
courses = get_fsgt42() + get_ffc() + get_fsgt69() + get_fsgt71()
courses = [el for el in courses if
    not el['cate'] in exclude_cates and
    (not 'type' in el or not el['type'] in exclude_types) and
    (not 'Rando' in el['nom']) and
    (not 'RANDO' in el['nom']) and
    (not 'BREVET' in el['nom'])
    ]


if args.f == 'forum':
    print(format_forum(courses,filter=True,tmpl=forum_template))
elif args.f == 'txt' :
    print(format_forum(courses,filter=False,tmpl=raw_template))
elif args.f == 'html' :
    print('''<!DOCTYPE html>
    <html>
    <head>
    <meta charset='UTF-8'>
    <style>
    body {font-family:Helvetica, Arial, sans-serif; font-size:14px;}
    table { border-collapse:collapse; }
    td { border:1px solid #666; }
    </style>
    </head>
    <body><table>''')
    print(format_forum(
        courses,
        filter=False,
        tmpl=html_template,
        dateTmpl=Template('<tr class="date"><td colspan="3">$date :</td></tr>')))
    print('</table></body></html>')