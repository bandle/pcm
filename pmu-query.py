#!/usr/bin/python
import urllib2
import json, csv
import subprocess
import sys
import platform
import getopt
import re

all_flag = False
download_flag = False
filename=None
events=[]

try:
    opts, args = getopt.getopt(sys.argv[1:],'a,f:,d',['all','file=','download'])
    for o, a in opts:
        if o in ('-a','--all'):
            all_flag=True
        if o in ('-f','--file'):
            filename=a
        if o in ('-d','--download'):
            download_flag=True
except getopt.GetoptError, err:
    print("parse error: %s\n" %(str(err)))
    exit(-2)

if filename == None:
    map_file_raw=urllib2.urlopen('https://download.01.org/perfmon/mapfile.csv')
    map_dict = csv.DictReader(map_file_raw)
    map_file = []
    paths = dict()

    while True:
        try:
            map_file.append(map_dict.next())
        except StopIteration:
            break

    # Get the current CPU
    if platform.system() == 'CYGWIN_NT-6.1':
        p = subprocess.Popen(['./pcm-core.exe -c'],stdout=subprocess.PIPE,shell=True)
    elif platform.system() == 'Windows':
        p = subprocess.Popen(['pcm-core.exe -c'],stdout=subprocess.PIPE,shell=True)
    else:
        p = subprocess.Popen(['./pcm-core.x -c'],stdout=subprocess.PIPE,shell=True)

    (output, err) = p.communicate()
    p_status = p.wait()

    # Find the corresponding event files
    for model in map_file:
        if re.search(model['Family-model'], output):
            paths[model['EventType']] = model['Filename']
            print (model)

    # Check if we at least found core events
    if not "core" in paths:
        print ('no core event found for %s CPU, program abort...' % (output))
        exit(-1)

    for eventType in paths:
        path = paths[eventType]
        json_data=urllib2.urlopen('https://download.01.org/perfmon'+path)
        events_data=json.load(json_data)
        if(download_flag == True):
            with open(path.split('/')[-1],'w') as outfile:
                json.dump(events_data, outfile, sort_keys=True, indent=4)
        events += events_data
else:
    for f in filename.split(','):
        print f
        events.extend(json.load(open(f)))

if all_flag == True:
    for event in events:
        if 'EventName' in event and 'BriefDescription' in event:
            print (event['EventName']+':'+event['BriefDescription'])
    sys.exit(0)

name=raw_input("Event to query (empty enter to quit):")
while(name != ''):
    for event in events:
        if event.has_key('EventName') and name.lower() in event['EventName'].lower():
            print (event['EventName']+':'+event['BriefDescription'])
            for ev_code in event['EventCode'].split(', '):
                print ('cpu/umask=%s,event=%s,name=%s%s%s%s%s%s/' % (
                        event['UMask'], ev_code, event['EventName'],
                        (',offcore_rsp=%s' % (event['MSRValue'])) if 'MSRValue' in event and event['MSRValue'] != '0' else '',
                        (',inv=%s' % (event['Invert'])) if 'Invert' in event and event['Invert'] != '0' else '',
                        (',any=%s' % (event['AnyThread'])) if 'AnyThread' in event and event['AnyThread'] != '0' else '',
                        (',edge=%s'% (event['EdgeDetect'])) if 'EdgeDetect' in event and event['EdgeDetect'] != '0' else '',
                        (',cmask=%s' % (event['CounterMask'])) if 'CounterMask' in event and event['CounterMask'] != '0' else ''))
    name=raw_input("Event to query (empty enter to quit):")
