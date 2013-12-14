from lxml import etree, objectify
from datetime import timedelta
from datetime import datetime
import os
import glob
import pprint
import json
import math
from pyproj import Proj, transform

stations = {}
#This turns inbound/outbound into a best guess direction
stations_hash = {
'BAK': {'inbound':'S',
        'outbound':'N',
        'name':'Bakerloo'},
'VIC': {'inbound':'S',
        'outbound':'N',
        'name':'Victoria'},
'NTN': {'inbound':'S',
        'outbound':'N',
        'name':'Northern'},
'CEN': {'inbound':'W',
        'outbound':'E',
        'name':'Central'},
'CIR': {'inbound':'CCW',
        'outbound':'CW',
        'name':'Circle'},
'DIS': {'inbound':'W',
        'outbound':'E',
        'name':'District'},
'HAM': {'inbound':'W',
        'outbound':'E',
        'name':'Ham & City'},
'JUB': {'inbound':'W',
        'outbound':'E',
        'name':'Jubilee'},
'MET': {'inbound':'W',
        'outbound':'E',
        'name':'Metropolitan'},
'PIC': {'inbound':'W',
        'outbound':'E',
        'name':'Piccadilly'},
'WAC': {'inbound':'W',
        'outbound':'E',
        'name':'W & City'},
'DLR': {'inbound':'W/N',
        'outbound':'E/S',
        'name':'DLR'}
}

def load_xml(filename, stations):
    '''
    Load a TXC xml file, create a dict of JourneyPatternSections,
    a dict of the stations and their locations.
    '''
    with open(filename) as f:
        xml = f.read()
    root = objectify.fromstring(xml)
    JPS = {}
    for e in root.JourneyPatternSections.iterchildren():
        JPS[e.attrib['id']] = e

    for sp in root.StopPoints.iterchildren():
        if not sp.AtcoCode in stations:
            stations[str(sp.AtcoCode)] = str(sp.Descriptor.CommonName)
            #strip the last number, assume platform?
            stations[str(sp.AtcoCode)[0:-1]] = {'easting':str(sp.Place.Location.Easting),
                                               'northing': str(sp.Place.Location.Northing)                                              }
    line = filename.split("-")[1][0:-1]
    return (JPS, root, stations, line)
        
def timeinseconds(string):
    '''
    Convert the TXC time string into seconds
    Formats seen PTxxS, PTxM, PTxMxxS
    '''
    string = str(string)
    a = string.split("PT")[1].split('S')[0].split("M")
    if len(a) == 2:
        time = int(a[0]) * 60
        try:
            time+= int(a[1])
        except ValueError:
            pass
    else:
        time = int(a[0])
    return time

def journey_parse(root, JPS, line, journeys, stations):
    '''
    The business bit, take each Journey and build
    a timetable
    '''
    for j in root.VehicleJourneys.iterchildren():
        d = {'time':str(j.DepartureTime),'jp_ref':str(j.JourneyPatternRef)}
        xp = "//JourneyPattern[@id='" + j.JourneyPatternRef + "']"
        d['direction'] = stations_hash[line][root.xpath(xp)[0].Direction]
        # We need this to find the time between stops
        d['jps_ref'] = str(root.xpath(xp)[0].JourneyPatternSectionRefs)
        d['line'] = stations_hash[line]['name']
        d['tt'] = {}
        days_l = []
        # Here are some scary assumptions...
        # Mon-Sat last tubes are same,
        # Sunday tubes after midnight are tagged
        # Monday, for now ignore Bank Hols.
        try:
           first_day = j.OperatingProfile.RegularDayType.DaysOfWeek.iterchildren().next().tag
        except AttributeError:
           first_day = "Holiday"
        if first_day == "Sunday":
            if int(d['time'][0:2]) > 3:
                days_l = ['Sunday']
            else:
                days_l = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        elif first_day == "Monday":
            if int(d['time'][0:2]) < 3:
                days_l = ['Sunday']
            else:
                days_l = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        else:
            days_l = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        d['days'] = days_l
        i = 0
        rt = 0
        #for each stop
        for jptl in JPS[d['jps_ref']].iterchildren():
            #if first stop
            if i == 0:
                #take the start time
                d['tt'][str(jptl.From.StopPointRef)] = str(d['time'])
                #add the time to the next stop
                rt += timeinseconds(jptl.RunTime)
                a = datetime.strptime(str(d['time']), "%H:%M:%S")
                try:
                    #add the wait at the next station (if it waits)
                    rt += timeinseconds(jptl.To.WaitTime)
                except AttributeError:
                    pass
                b = timedelta(seconds = rt)
                d['tt'][str(jptl.To.StopPointRef)] = (a + b).time().strftime("%H:%M:%S")
            else:
                rt += timeinseconds(jptl.RunTime) 
                a = datetime.strptime(str(d['time']), "%H:%M:%S")
                try:
                    rt += timeinseconds(jptl.To.WaitTime)
                except AttributeError:
                    pass
                b = timedelta(seconds = rt)
                d['tt'][str(jptl.To.StopPointRef)] = (a + b).time().strftime("%H:%M:%S")
            i+=1
        d['destination'] = str(stations[jptl.To.StopPointRef])
        #pop the destination (as you can't take a tube nowhere)
        d['tt'].pop(str(jptl.To.StopPointRef))
        journeys.append(d)
    return journeys

def get_last(station, day, stations, journeys):
    '''
    Find the last tube at a given station,
    on a given day.
    '''
    ret = []
    t = {}
    for j in journeys:
        to_add = None
        #if the journey is today
        if day in j['days']:
            try:    	    
                #and it passes our station
                to_add = (j['tt'][station], j['destination'])
            except KeyError:
                pass
            if to_add:
                #build a dict of line/direction/(time,destingation)
                #for our station
                try:
                    t[j['line']][j['direction']].append(to_add)
                except KeyError as e:
                    if e[0] == j['line']:
                        t[j['line']] = {}
                        t[j['line']][j['direction']] = []
                    else:
                        t[j['line']][j['direction']] = []
                    t[j['line']][j['direction']].append(to_add)
      
    for line, directions in t.items():
        for direction, times in directions.items():
           last = [] 
           for time in times:
               #times after midnight before 4 are last
               if time[0][0:2] in ['00','01','02','03']:
                   last.append(time)
           if last == []:
               ret.append({'station':stations[station], 'line':line, 'direction':direction, 'last':sorted(times)[-1]})
           else:
               ret.append({'station':stations[station], 'line':line, 'direction':direction, 'last':sorted(last)[-1]})
    return ret

def get_last_all(station, day, stations, journeys):
    '''
    because platform numbers are added to station codes
    loop through 0 to 9 to catch all lines at that station
    '''
    out = []
    out += get_last(station, day, stations, journeys)
    for i in range(0,9):
        s = station + str(i)
        out += get_last(s, day, stations, journeys)
    return out

journeys = []
stations = {}
mtime = os.path.getmtime('journeys.txt')

def load_data():
    '''
    Create the journey/station data if
    it doesn't exits, else read in.
    '''
    try:
        with open('journeys.txt') as infile:
            journeys = json.load(infile) 
    except IOError:
        for filename in glob.glob("./data/*.xml"):
            JPS, root, stations, line = load_xml(filename, stations)
            journeys = journey_parse(root, JPS, line, journeys, stations)
        with open('journeys.txt', 'w') as outfile:
            json.dump(journeys, outfile)
    try:
        with open('stations.txt', 'r') as infile:
                stations = json.load(infile)
    except IOError:  
        old_stations = {}
        for filename in glob.glob("./data/*.xml"):
            old_stations = stations
            JPS, root, stations, line = load_xml(filename, stations)
            stations = dict(old_stations.items()+stations.items())
        with open('stations.txt', 'w') as outfile:
            json.dump(stations, outfile)
    return (stations, journeys)

def reload_data():
    '''
    To force reload.
    '''
    journeys = []
    stations = {}
    for filename in glob.glob("./data/*.xml"):
        JPS, root, stations, line = load_xml(filename, stations)
        journeys = journey_parse(root, JPS, line, journeys, stations)
    
    with open('journeys1.txt', 'w') as outfile:
        json.dump(journeys, outfile)
    old_stations = {}
    for filename in glob.glob("./data/*.xml"):
        old_stations = stations
        JPS, root, stations, line = load_xml(filename, stations)
        stations = dict(old_stations.items()+stations.items())
    with open('stations1.txt', 'w') as outfile:
        json.dump(stations, outfile)
    os.remove('stations.txt')
    os.rename('stations1.txt', 'stations.txt')
    os.remove('journeys.txt')
    os.rename('journeys1.txt', 'journeys.txt')

    return True


v84 = Proj(proj="latlong",towgs84="0,0,0",ellps="WGS84")
v36 = Proj(proj="latlong", k=0.9996012717, ellps="airy",
        towgs84="446.448,-125.157,542.060,0.1502,0.2470,0.8421,-20.4894")
vgrid = Proj(init="world:bng")


def ENtoLL84(easting, northing):
    """Returns (longitude, latitude) tuple
    """
    vlon36, vlat36 = vgrid(easting, northing, inverse=True)
    return transform(v36, v84, vlon36, vlat36)

def LL84toEN(longitude, latitude):
    """Returns (easting, northing) tuple
    """
    vlon36, vlat36 = transform(v84, v36, longitude, latitude)
    return vgrid(vlon36, vlat36)

def nearest_stations(lat,lon,number,stations):
    '''
    Find the number of nearest stations
    to a lat/lon.
    '''
    my_e = LL84toEN(lon,lat)[0]
    my_n = LL84toEN(lon,lat)[1]
    near_list = []
    for station, value in stations.items():
        try:
            e = float(value['easting'])
            n = float(value['northing'])
            dist = float(math.sqrt(((e - my_e)**2) + ((n - my_n)**2)))
            near_list.append((dist, station))
        except TypeError:
            pass
    near_list = sorted(near_list)[0:number]
    return near_list        
