#!/usr/bin/env python
# Example parser written for getting data from http://meteo.pg.gda.pl

import urllib2
import re
import psycopg2
import sys

import config

METEO_URL = 'http://meteo.pg.gda.pl'

def prepareData(data):
	values = re.findall(r"[-+]?\d*\.\d+|\d+", data)
	if len(values) == 1:
		return values[0]
	else:
		return null;

def insertData(conn, temp, hum):
	query =  "INSERT INTO %s (temperature, humidity)" % (config.dbtable) + " VALUES (%s, %s);"
	cursor = conn.cursor()
	data = (temp, hum)
	cursor.execute(query, data)
	conn.commit()

try:
	meteoSource = urllib2.urlopen(METEO_URL).readlines()
except:
	#print "I am unable to connect to " + METEO_URL
	sys.exit(1)

if len(meteoSource) > 0:
	try:
                cs = "host=%s dbname=%s user=%s password=%s" % (config.host, config.dbname, config.user, config.password)
                conn = psycopg2.connect(cs)
	except:
		print "I am unable to connect to the database"
		sys.exit(1)
	temp = -1
	humidity = -1
	tempValue = 0
	humValue = 0
	for line in meteoSource:
		if '<strong>Temperature:</strong>' in line:
			temp = 6
		if '<strong>Humidity:</strong>' in line:
			humidity = 6
		if temp >= 0:
			temp -= 1
		if humidity >= 0:
			humidity -= 1
		if temp == 0:
			tempValue = prepareData(line.strip())
		if humidity == 0:
			humValue = prepareData(line.strip())

	insertData(conn, tempValue, humValue)
