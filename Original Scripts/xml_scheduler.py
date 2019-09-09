#################################################################################
# Copyright 2019 University of Cologne Licensed under the Educational           #
# Community License, Version 2.0 (the "License"); you may not use this file     #
# except in compliance with the License. You may obtain a copy of the License at#
#                                                                               #
# http://opensource.org/licenses/ECL-2.0                                        #
#                                                                               #
#  Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT     #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the      #
# License for the specific language governing permissions and limitations under #
# the License.                                                                  #
#                                                                               #
################################################################################# 
#                                                                               #
# XML Scheduler script from                                                           #
# Author: Maximiliano Lira Del Canto                                            #
# Date: September 2019                                                          #
#                                                                               #
#################################################################################

# XML Scheduler
# Maximiliano Lira Del Canto
# Universitat zu Koeln
# July 2019


import argparse
import datetime as dt
import json
import pytz
import re
import requests
import sys
import xml.etree.ElementTree as ET


# Argument parser
parser = argparse.ArgumentParser(description='Schedule events in the opencast cluster. \
The schedule information comes from the Klips system as a XML file.') 

#Arguments and description
parser.add_argument('server_url', type=str,
                    help ='URL of the opencast ***REMOVED*** server')

parser.add_argument('username', type=str,
                    help='Opencast Username')

parser.add_argument('password', type=str,
                    help ='Opencast Password')

parser.add_argument('archive_path', type=str,
                    help ='The XML file with the event list')

parser.add_argument('seriesID', type=str,
                    help ='The Series ID of the event')

parser.add_argument('--normalizeaudio',help= "Enable normalize audio",
                    default = False, action='store_true') 

parser.add_argument('--publishtocms', help='Publish to CMS',
                    default = False, action='store_true') 

parser.add_argument('--enabledownload', help='Create download links',
                    default = False, action='store_true')

parser.add_argument('--createsbs', help='Create Side-by-Side version',
                    default = False, action='store_true')


parser.add_argument('--enableannotation', help='Enable Annotation Tool',
                    default = False, action='store_true')


parser.add_argument('--autopublish', help='Publish without editing',
                    default = False, action='store_true')


parser.add_argument('--publishlive', help='Schedule a live event',
                    default = False, action='store_true')


parser.add_argument('--track4k', help='Enable automatic tracking for 4K videos',
                    default = False, action='store_true')


parser.add_argument('--nocamera',help='Disable camera recording (Only for Galicaster CA)',
                    dest='camera', default = False, action='store_true')

parser.add_argument('--nobeamer', help='Disable recording from the proyector (Only Galicaster CA)',
                    dest='beamer', default = False, action='store_true')

parser.add_argument('--noaudio', dest='audio', help='Disable audio recording (Only for Galicaster CA)',
                    default = False, action='store_true')

parser.add_argument('--test', default = False, action='store_true',
                    help='Enable test mode: Shows the request body without sending it')

parser.add_argument('--forceCA', type=str, metavar='CapAgName', 
                    help='Forces the use a different capture agent expressed by CapAgName variable')

args = parser.parse_args()



# Helper functions
def inverseName (invertedName):
    try:
        strippedTitle = invertedName.rpartition(';')[0]
        stdName = ';'.join([("%s, %s" % (fn, ln)) for ln, fn in [tuple(k.split(",")) for k in strippedTitle.split(";")]]).strip().replace(",","")
    except AttributeError:
        stdName = "Null"
    return stdName

def get_acl(serverURL, OCUser, OCPass, seriesID):
    url = "https://" + serverURL + "/api/series/"+ seriesID +"/acl"

    credentials = (OCUser, OCPass)

    headers = {
        'Authorization': "Basic",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': serverURL,
        'accept-encoding': "gzip, deflate",
        'Connection':'close',
        'cache-control': "no-cache"
        }
    try:
        response = requests.request("GET", url, headers=headers, auth=credentials)
    except requests.exceptions.ConnectionError as e:
        sys.stderr.write('Failed to establish a new connection \n')
        sys.stderr.write('Check the URL and connection of Opencast \n')
        sys.stderr.write("Exception: %s" % str(e))
        sys.exit(1)

    if response.status_code == 401:
        print ('Bad credentials: Please check the username and password')

    try:
        return response.json()
    except json.decoder.JSONDecodeError as e:
        sys.stderr.write('Can\'t parse json output or there is no output \n')
        sys.stderr.write('Check that the seriesID is correct \n')
        sys.stderr.write("Exception: %s" % str(e))
        sys.exit(1)
def getStartTime(xmlRow, minBefore):
    #Get the date and start time
    date = xmlRow.find('DATUM').text
    startTime = xmlRow.find('VON').text

    #Convert to datetime format
    date_time = date + ' ' + startTime
    datetimeObj = dt.datetime.strptime(date_time, '%d.%m.%Y %H:%M')
    local = pytz.timezone('Europe/Berlin')
    local_time = local.localize(datetimeObj)
    utc_time=local_time.astimezone(pytz.utc) - dt.timedelta(hours=0, minutes=minBefore)
    
    # Return the time in UTC and with the minutes correction
    return utc_time.isoformat()[:-6] + 'z'

def getEndTime(xmlRow, minAfter):
    #Get the date and start time
    date = xmlRow.find('DATUM').text
    endTime = xmlRow.find('BIS').text

    #Convert to datetime formatpen
    date_time = date + ' ' + endTime
    datetimeObj = dt.datetime.strptime(date_time, '%d.%m.%Y %H:%M')
    local = pytz.timezone('Europe/Berlin')
    local_time = local.localize(datetimeObj)
    utc_time=local_time.astimezone(pytz.utc) + dt.timedelta(hours=0, minutes=minAfter)
    
    # Return the time in UTC and with the minutes correction
    return utc_time.isoformat()[:-6] + 'z'

def getAgentID(serverURL, OCUser, OCPass):
    #Get the list of the available capture agents in the Opencast Cluster
    url = "https://" + serverURL + "/api/agents"
    credentials = (OCUser, OCPass)

    headers = {
        'Authorization': "Basic",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': serverURL,
        'accept-encoding': "gzip, deflate",
        'Connection':'close',
        'cache-control': "no-cache"
        }

    response = requests.request("GET", url, headers=headers, auth=credentials)
    agentListJson = response.json()
    return agentListJson
    
    
def roomAgent(xmlRow, agentListJson):   
    agentList = []
    for agent in agentListJson:
        agentList.append(agent["agent_id"])
    

    # Get the building and room number
    location = xmlRow.find('ORT').text
    regex = r"\(([^)]+)\)(?!.*(\(([^)]+)\)))"
    match = re.search(regex, location)
    BuildRoom = match.group(1).replace('.','').split("/")
    
    if args.test == True:
        print("Location of the lecture: ", location)
        print ("Building: ", BuildRoom[0])
        print ("Room: ", BuildRoom[2] + '\n')

    # Compare with the list
    if args.forceCA == None:
        agentMatch = None
        for agent in agentList:
            ca = agent.split('-')
            # If get a match, return the capture agent name
            try:
                if (ca[1] == BuildRoom[0]) and (ca[2]== BuildRoom[2]):
                    agentMatch = agent
            except IndexError:
                continue
        if agentMatch == None:
            print ('Warning, there is no capture agent for building ' + BuildRoom[0] +' in \
room '+ BuildRoom[2] + '\n')
        return agentMatch
    
    # If there is no match, set the mobile capture agent
    return args.forceCA

def getInputs(camera, beamer, audio):
    inputs =["defaults"]    
    if camera == False:
        inputs.append("Camera")
    if beamer == False:
        inputs.append("Beamer")
    if audio == False:
        inputs.append("Ton")
    return inputs


# Get and parse XML file
def XmlGP (xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    return root

# Create the payload for the API post
def payload (xmlRow, args, acl, agents):
    
    
    # Create the metadata payload
    metadata = [
        {
            "flavor": "dublincore/episode",
            "fields": []    
        }
    ]
    
    # Properties to add to metadata, title, creator, comments, series ID
    title = {"id":"title", "value": xmlRow.find('LV_NUMMER').text + ' ' + xmlRow.find('TITEL').text + ' ' + xmlRow.attrib['NUM']}
    creator = { "id":"creator", "value": [inverseName(xmlRow.find('VORTRAGENDER_KONTAKTPERSON').text)]} 
    try:
        if xmlRow.find('ANMERKUNG').attrib['NULL'] == 'TRUE':
            description = {"id":"description", "value":"None"}
    except KeyError:
        description = {"id":"description", "value": xmlRow.find('ANMERKUNG').text}
    seriesID = {"id":"isPartOf", "value": args.seriesID}

    # Append to metadata
    metadata[0]['fields'].append(title)
    metadata[0]['fields'].append(creator)
    metadata[0]['fields'].append(description)
    metadata[0]['fields'].append(seriesID)

    # Create the processing payload
    processing = {
        "workflow": "schedule-and-upload",
        "configuration": {
            "normalizeAudio": str(args.normalizeaudio).lower(), 
            "publishToCMS": str(args.publishtocms).lower(),
            "createSBS": str(args.createsbs).lower(),
            "enableDownload":str(args.enabledownload).lower(),
            "enableAnnotation": str(args.enableannotation).lower(),
            "autopublish":str(args.autopublish).lower(),
            "publishLive":str(args.publishlive).lower(),
            "track4K":str(args.track4k).lower()
        }
    }


    # Create the scheduling payload
    scheduling = {
        "agent_id": roomAgent(xmlRow, agents),
        "start": getStartTime(xmlRow,5),
        "end": getEndTime(xmlRow, 10),
        "inputs": getInputs(args.camera, args.beamer, args.audio)
    }
    
    data = [json.dumps(metadata), 
            json.dumps(acl), 
            json.dumps(processing), 
            json.dumps(scheduling)
            ]

    return  data


# Post the API request
def post(args, data):
    url = "https://" + args.server_url + "/api/events"

    credentials = (args.username, args.password)

    body = {
        "metadata": (None, data[0]),
        "acl": (None, data[1]),
        "processing": (None, data[2]),
        "scheduling": (None, data[3])
    }

    headers = {
    'content-disposition': "form-data",
    'cache-control': "no-cache",
    'Connection':'close'
    }

    if args.test == True:
        print('Query headers (Pretty print)')
        print(json.dumps(headers, indent=4))


        print('To be sent in the body (Pretty print)')
        print (json.dumps(body, indent=4))
        print('----------------------------------')
        print(json.loads(data[0])[0]['fields'][0]['value'])
        print('----------------------------------')
        print()
        print()


    if args.test == False:
        response = requests.post (url, files=body, headers=headers, auth=credentials)
        if response.status_code == 201:
            print(json.loads(data[0])[0]['fields'][0]['value'] + ' was succesfully created.')
            print( 'Event identifier: ' + json.loads(response.text)['identifier'] + '\n')
        elif response.status_code == 400:
            print('Bad Request: Error 400. Event title: ' + json.loads(data[0])[0]['fields'][0]['value'])
            print('Please check their options and try again, if persists, call the ***REMOVED***istrator.')
            print('Details of the error: ' + response.content.decode("utf-8"))
            if  response.content.decode("utf-8").lower() == 'Unable to parse device'.lower():
                print('Hint: This error could be caused by the naming setup of the capture agent' + '\n')
        elif response.status_code == 409:
            print('Scheduling conflict: Error 409. Event title: ' + json.loads(data[0])[0]['fields'][0]['value'])
            print('There is a conflict with other event scheduled between ' + json.loads(data[3])['start'] + ' UTC and \
' + json.loads(data[3])['end'] + ' UTC in the same capture agent, reschedule this event or modify the existing one. \n' )
##############################

## Main program

# Parse XML File
parsedXml = XmlGP(args.archive_path)

# Get ACL list
acl = get_acl(args.server_url, args.username, args.password, args.seriesID)

# Get Capture Agent list
agents = getAgentID(args.server_url, args.username, args.password)

# Post each lecture in the XML file
for row in parsedXml:
    data = payload(row, args, acl, agents)
    post(args, data)

##############################


