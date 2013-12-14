from lxml import etree, objectify
from datetime import timedelta
from datetime import datetime
import os
import glob
import pprint
import json
import math

stations = {}
in_out_hash = {
'BAK': {'inbound':'S',
        'outbound':'N'},
'VIC': {'inbound':'S',
        'outbound':'N'},
'NTN': {'inbound':'S',
        'outbound':'N'},
'CEN': {'inbound':'W',
        'outbound':'E'},
'CIR': {'inbound':'CCW',
        'outbound':'CW'},
'DIS': {'inbound':'W',
        'outbound':'E'},
'HAM': {'inbound':'W',
        'outbound':'E'},
'JUB': {'inbound':'W',
        'outbound':'E'},
'MET': {'inbound':'W',
        'outbound':'E'},
'PIC': {'inbound':'W',
        'outbound':'E'},
'WAC': {'inbound':'W',
        'outbound':'E'},
'DLR': {'inbound':'W/N',
        'outbound':'E/S'}
}

def load_xml(filename, stations):
    with open(filename) as f:
        xml = f.read()
    root = objectify.fromstring(xml)
    JPS = {}
    for e in root.JourneyPatternSections.iterchildren():
        JPS[e.attrib['id']] = e

    for sp in root.StopPoints.iterchildren():
        if not sp.AtcoCode in stations:
            stations[str(sp.AtcoCode)] = str(sp.Descriptor.CommonName)
            stations[str(sp.AtcoCode)[0:-1]] = {'easting':str(sp.Place.Location.Easting),
                                               'northing': str(sp.Place.Location.Northing)                                              }
    line = filename.split("-")[1][0:-1]
    return (JPS, root, stations, line)
        
def timeinseconds(string):
    string = str(string)
    a = string.split("PT")[1].split('S')[0].split("M")
    if len(a) == 2:
        time = int(a[0]) * 60
        try:
            time+= int(a[1])
#            if int(a[1]) == 30:
#                print "adding 30"
#                time += 30
        except ValueError:
            pass
    else:
        time = int(a[0])
    return time

def journey_parse(root, JPS, line, journeys, stations):
    for j in root.VehicleJourneys.iterchildren():
        d = {'time':str(j.DepartureTime),'jp_ref':str(j.JourneyPatternRef)}
#        if str(j.DepartureTime)[-2:] == "30":
#            delta = timedelta(seconds = 30)
#            orig = datetime.strptime(str(j.DepartureTime), "%H:%M:%S")
#            time = (delta + orig).time().strftime("%H:%M:%S")
#            d['time'] = time
        xp = "//JourneyPattern[@id='" + j.JourneyPatternRef + "']"
        d['direction'] = in_out_hash[line][root.xpath(xp)[0].Direction]
        d['jps_ref'] = str(root.xpath(xp)[0].JourneyPatternSectionRefs)
        d['line'] = line
        d['tt'] = {}
        days_l = []
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
#        for days in j.OperatingProfile.RegularDayType.DaysOfWeek.iterchildren():
#            #if days.tag == "Sunday":
#            #    days_l = ['Sunday']
#            if days.tag == "Monday" or days.tag == "MondayToFriday":
#                days_l = ['Sunday']
#            else:
#                days_l = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        d['days'] = days_l
        i = 0
        rt = 0
        for jptl in JPS[d['jps_ref']].iterchildren():
            #if i + 1 == len(JPS[d['jps_ref']].iterchildren()):
            #    break
            if i == 0:
    #             d['tt'][i] = {'station':jptl.From.StopPointRef, 'time': d['time']}
                d['tt'][str(jptl.From.StopPointRef)] = str(d['time'])
                rt += timeinseconds(jptl.RunTime)
                a = datetime.strptime(str(d['time']), "%H:%M:%S")
                try:
                    rt += timeinseconds(jptl.To.WaitTime)
                except AttributeError:
                    pass
                b = timedelta(seconds = rt)
    #             d['tt'][i+1] = {'station':jptl.To.StopPointRef, 'time': (a + b).time().strftime("%H:%M:%S")}            
                d['tt'][str(jptl.To.StopPointRef)] = (a + b).time().strftime("%H:%M:%S")
            else:
                rt += timeinseconds(jptl.RunTime) 
                a = datetime.strptime(str(d['time']), "%H:%M:%S")
                try:
                    rt += timeinseconds(jptl.To.WaitTime)
                except AttributeError:
                    pass
                b = timedelta(seconds = rt)
    #             d['tt'][i+1] = {'station':jptl.To.StopPointRef, 'time': (a + b).time().strftime("%H:%M:%S")} 
                d['tt'][str(jptl.To.StopPointRef)] = (a + b).time().strftime("%H:%M:%S")
            i+=1
        d['destination'] = str(stations[jptl.To.StopPointRef])
        d['tt'].pop(str(jptl.To.StopPointRef))
        journeys.append(d)
    return journeys

def get_last(station, day, stations, journeys):
    ret = []
    t = {}
    for j in journeys:
        to_add = None
        if day in j['days']:
            try:    	    
                to_add = (j['tt'][station], j['destination'])
            except KeyError:
                pass
            if to_add:
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
               if time[0][0:2] in ['00','01','02','03']:
                   last.append(time)
           if last == []:
               ret.append({'station':stations[station], 'line':line, 'direction':direction, 'last':sorted(times)[-1]})
           else:
               ret.append({'station':stations[station], 'line':line, 'direction':direction, 'last':sorted(last)[-1]})
    return ret

def get_last_all(station, day, stations, journeys):
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
    try:
        with open('journeys.txt') as infile:
            journeys = json.load(infile) 
    except IOError:
        for filename in glob.glob("./data/*.xml"):
            JPS, root, stations, line = load_xml(filename, stations)
            journeys = journey_parse(root, JPS, line, journeys, stations)
    #
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

from pyproj import Proj, transform

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
