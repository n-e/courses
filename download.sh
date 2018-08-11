#!/bin/sh

set -e

FOLDER=`date +'%Y-%m-%d'`

mkdir -p $FOLDER
cd $FOLDER

FFC='http://www.auvergnerhonealpescyclisme.com/route/calendrier'
FFCLOISIR='http://auvergnerhonealpescyclisme.com/cyclisme-pour-tous/calendrier'
FSGT69='http://www.cyclismerhonefsgt.fr/calendrier/'
FSGT42='http://www.fsgt42.com/cyclisme/index.php?page=listecourses'
FSGT71='http://www.fsgt71velo.fr/2018/calendrier/calendrier.html'

curl "$FFC" > calffc.html
curl "$FFCLOISIR" > calffcl.html
curl "$FSGT69" > cal69.html
curl "$FSGT42" > cal42.html
curl "$FSGT71" > cal71.html