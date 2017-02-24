#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import psycopg2
import json
import datetime
import gviz_api

reload(sys)  
sys.setdefaultencoding('utf8')

import config

page_template = """
<html>
<head>
  <script src="https://www.google.com/jsapi" type="text/javascript"></script>
  <script type="text/javascript">
    google.load('visualization', '1', {packages:['corechart']});

    google.setOnLoadCallback(drawCharts);
    function drawCharts() {
      drawChart('chart1day', %(json1day)s, 'Ostatni dzień');
      drawChart('chart7days', %(json7days)s, 'Ostatni tydzień');
      drawChart('chart365days', %(json365days)s, 'Ostatni rok');
    }

    function drawChart(div, json, titleString) {
      var options = {
        title: titleString,
        curveType: 'function',
        legend: { position: 'bottom' },
        colors: ['red', 'blue'],
        xAxis: {format: 'Date'},
        vAxes: {
          0: {logScale: false},
          1: {logScale: false, format: 'percent'}
        },
        series: {
          0: {targetAxisIndex: 0},
          1: {targetAxisIndex: 1}
        },
      };

      var data = new google.visualization.DataTable(json);
      var formatter = new google.visualization.NumberFormat({
        fractionDigits: 2,
        pattern: '#,###%%'
      });
      formatter.format(data, 2);

      var chart = new google.visualization.LineChart(document.getElementById(div));
      chart.draw(data, options);
    }
  </script>
  <title>Temperatura i wilgotność w Gdańsku Wrzeszczu</title>
</head>
<body>
  <div id="chart1day"></div>
  <div id="chart7days"></div>
  <div id="chart365days"></div>
</body>
</html>
"""

def getData(start, limit):
  try:
    cs = "host=%s dbname=%s user=%s password=%s" % (config.host, config.dbname, config.user, config.password)
    conn = psycopg2.connect(cs)
  except:
    print "I am unable to connect to the database"

  cur = conn.cursor()
  if limit <= 4*24*7:
    cur.execute('SELECT extract(epoch from date), temperature, humidity from pg order by date desc limit ' + str(limit) + ' OFFSET ' + str(start))
  else:
    cur.execute('SELECT t.* FROM (SELECT extract(epoch from date), temperature, humidity, row_number() OVER(ORDER BY date DESC) AS row from pg limit ' + str(limit) + ' OFFSET ' + str(start) + ') t WHERE t.row % ' + str(limit/2920)  + ' = 0')
  rows = cur.fetchall()

  jsonData = []
  for row in rows:
    jsonData.append({'timestamp': row[0], 'date': datetime.datetime.fromtimestamp(int(row[0])), 'temperature': row[1], 'humidity': (float(row[2])/100)})

  return jsonData

def createJson(start, limit):
  description = {
    "timestamp": ("number", "Timestamp"),
    "date": ("datetime", "Data"),
    "temperature": ("number", "Temperatura"),
    "humidity": ("number", "Wilgotność"),
  }

  jsonData = getData(start, limit)

  # Loading it into gviz_api.DataTable
  data_table = gviz_api.DataTable(description)
  data_table.LoadData(jsonData)

  return data_table.ToJSon(columns_order=("date", "temperature", "humidity"), order_by="timestamp")

def main():
  # Create a JSON string.
  json1day = createJson(0, 4*24)
  json7days = createJson(0, 4*24*7)
  json365days = createJson(0, 4*24*365)

  # Put the JS code and JSON string into the template.
  print "Content-Type: text/html;charset=utf-8"
  print
  print page_template % {'json1day': json1day, 'json7days': json7days, 'json365days': json365days}


if __name__ == '__main__':
  main()
