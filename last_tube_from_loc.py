import json
import os
import last_tube
from datetime import timedelta
from datetime import datetime
from flask import Flask
app = Flask(__name__)

stations, journeys = last_tube.load_data()
mtime = os.path.getmtime('journeys.txt')

@app.route('/getstn/<incode>')
def get_last_by_code(incode):
    global mtime
    if os.path.getmtime('journeys.txt') > mtime:
        global stations
        global journeys
        mtime = os.path.getmtime('journeys.txt')
        stations, journeys = last_tube.load_data()
    day = datetime.now().strftime('%A')
    aday = timedelta(days = 1)
    #If it's after midnight we still want "Todays'" last tube
    if datetime.now().hour >= 0 and datetime.now().hour < 4:
        day = (datetime.now() - aday).strftime('%A')
    codes = [incode]
    out = []
    for code in codes:
        print(code)
        out += last_tube.get_last_all(code, day, stations, journeys)
    return json.dumps(out)

@app.route('/getname/<name>')
def get_last_by_name(name):
    global mtime
    #If the journeys have been reloaded then read again.
    if os.path.getmtime('journeys.txt') > mtime:
        global stations
        global journeys
        mtime = os.path.getmtime('journeys.txt')
        stations, journeys = last_tube.load_data()
    codes = last_tube.station_from_name(name, stations)
    day = datetime.now().strftime('%A')
    aday = timedelta(days = 1)
    #If it's after midnight we still want "Todays'" last tube
    if datetime.now().hour >= 0 and datetime.now().hour < 4:
        day = (datetime.now() - aday).strftime('%A')
    out = []
    for code in codes:
        out += last_tube.get_last_all(code, day, stations, journeys)
    return json.dumps(out)

@app.route('/get/<lat>/<lon>')
def get_last_by_loc(lat,lon):
    global mtime
    #If the journeys have been reloaded then read again.
    if os.path.getmtime('journeys.txt') > mtime:
        global stations
        global journeys
        mtime = os.path.getmtime('journeys.txt')
        stations, journeys = last_tube.load_data()
    lat = str(lat)
    lon = str(lon)
    codes = last_tube.nearest_stations(lat,lon,3,stations)
    day = datetime.now().strftime('%A')
    aday = timedelta(days = 1)
    #If it's after midnight we still want "Todays'" last tube
    if datetime.now().hour >= 0 and datetime.now().hour < 4:
        day = (datetime.now() - aday).strftime('%A')
    out = []
    for code in codes:
        out += last_tube.get_last_all(code[1], day, stations, journeys)
    return json.dumps(out)

@app.route('/test.html')
def load():
    with open("./test.html", 'r') as infile:

      return infile.read()

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
