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
# Program to schedule events using a XML file retrieved form the KLIPS system   #
# Author: Maximiliano Lira Del Canto                                            #
# Date: September 2019                                                          #
#                                                                               #
#################################################################################


import datetime as dt
import json
import pytz
import re
import requests
import sys
import xml.etree.ElementTree as ET



class args:
    def __init__(self):
        self.username = None
        self.password = None
        self.serverUrl = None
        self.seriesID = None
        self.timezone = None
        self.normalizeaudio = None
        self.publishtocms = None
        self.enabledownload = None
        self.createsbs = None
        self.enableannotation = None
        self.autopublish = None
        self.publishlive = None
        self.track4k = None
        self.nocamera = None
        self.nobeamer = None
        self.noaudio = None
        self.test = None
        self.forceCA = None
        self.dictCA = None

## Helper functions ##
#

# Invert the name order form "Last, First; Title" to "First Last"
def inverseName (invertedName):
    try:
        strippedTitle = invertedName.rpartition(';')[0]
        stdName = ';'.join([("%s, %s" % (fn, ln)) for ln, fn in [tuple(k.split(",")) for k in strippedTitle.split(";")]]).strip().replace(",","")
    except AttributeError:
        stdName = "Null"
    except ValueError:
        split_name = invertedName.split(",")
        stdName = split_name[1][1:] + " " + split_name[0]
    except:
        stdName = invertedName
    return stdName


# Get the ACL from the series
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
        message = 'Error: Failed to stablish connection to the server'
        code = 1
        return {"json":{}, "message":message, "code":code}

    if response.status_code == 401:
        message = "Error: Internal server error"
        sys.stderr.write('Bad credentials: Please check the username and password')
        code = 1
        return {"json":{}, "message":message, "code":code}


    try:
        resp = response.json() 
        code = 0
        message = 'Succesfully retreived ACLs'
        return {"json":resp, "message":message, "code":code}
    except json.decoder.JSONDecodeError as e:
        code = 1
        sys.stderr.write('Can\'t parse json output or there is no output \n')
        sys.stderr.write('Check that the seriesID is correct \n')
        sys.stderr.write("Exception: %s" % str(e))
        message = 'Error: Can\'t parse ACLs data, check that the series ID is correct or exists'
        return {"json":{}, "message":message, "code":code}
    except:
        code = 1
        sys.stderr.write('Unhandled error \n')
        message = 'Error getting the ACLs (Unhandled error), check that the series ID is correct'
        return {"json":{}, "message":message, "code":code}


        

# Get event start time from the XML file
def getStartTime(xmlRow, minBefore, tzone):
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

# Get event end time from the XML file
def getEndTime(xmlRow, minAfter, tzone):
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

# Get the list of the agent id registered in the opencast admin node
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
    

# Get the room code to get the desired capture agent from the diccionary set in properties.py
# Note: this will be ommited if in the form is set to Force the capture Agent
def roomAgent(args, xmlRow, agentListJson):   
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
        print ("List of agents:" + str(agentList))
        print ("Forced Capture agent: " + args.forceCA)


    
    #If there is no forced capture agent
    if args.forceCA == "None":
        agentMatch = None
        # Get CA from the dictionary in Django Settings
        try:
            agentMatch = args.dictCA[match.group(1)]
        except KeyError:
            agentMatch = None
            message = 'Error, there is no capture agent for building ' + BuildRoom[0] +' in room '+ BuildRoom[2]
            sys.stderr.write (message + '\n')
            return {"code": 1, "message": message, "agent": "Null"}


#######################################################################################################
# Algorithm to get automatically without diccionary the capture agent
# This only works if the room number is the same set in the capture agent.
# It was replaced for a manual diccionary. Left in the code for future reference
#
#
#         for agent in agentList:
#             ca = agent.split('-')
#             # If get a match, return the capture agent name
#             try:
#                 if (ca[1] == BuildRoom[0]) and (ca[2]== BuildRoom[2]):
#                     agentMatch = agent
#                     print ("selected agent: %s" % agent)
#                     break
#             except IndexError:
#                 continue
#         if agentMatch == None:
#             message = 'Error, there is no capture agent for building ' + BuildRoom[0] +' in \
# room '+ BuildRoom[2]
#             sys.stderr.write (message + '\n')
#             return {"code": 1, "message": message, "agent": "Null"}
########################################################################################################
        
        message = "Found capture agent in room"
        return {"code": 0, "message": message, "agent": agentMatch}
    
    # Set the forced capture agent
    message = "Using forced capture agent"
    return {"code": 0, "message": message, "agent": args.forceCA}



#Get a tuple ('agent', 'agent') for the ChoiceField function in the Django framework 
def agentToChoices(args):
    agentListJson = getAgentID(args.oc_url, args.oc_user, args.oc_passwd)
    agentList = []
    for agent in agentListJson:
        agentList.append(agent["agent_id"])
    choices = zip(agentList, agentList)
    choices.insert(0,(None, 'No force agent'))
    return choices


# Get what inputs in a galicaster CA will be activated
def getInputs(nocamera, nobeamer, noaudio):
    inputs =["defaults"]    
    if nocamera == False:
        inputs.append("Camera")
    if nobeamer == False:
        inputs.append("Beamer")
    if noaudio == False:
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

    selectAgent = roomAgent(args, xmlRow, agents)

    if selectAgent["code"] == 1:
        return selectAgent


    # Create the scheduling payload
    scheduling = {
        "agent_id": selectAgent["agent"],
        "start": getStartTime(xmlRow,5,args.timezone),
        "end": getEndTime(xmlRow, 10, args.timezone),
        "inputs": getInputs(args.nocamera, args.nobeamer, args.noaudio)
    }
    
    data = [json.dumps(metadata), 
            json.dumps(acl), 
            json.dumps(processing), 
            json.dumps(scheduling)
            ]

    return  data


# Post the API request
def post(args, data):
    url = "https://" + args.serverUrl + "/api/events"

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
            sys.stdout.write(json.loads(data[0])[0]['fields'][0]['value'] + ' was succesfully created.')
            sys.stdout.write( 'Event identifier: ' + json.loads(response.text)['identifier'] + '\n')
            message = json.loads(data[0])[0]['fields'][0]['value'] + ' was succesfully created. ' + 'Event identifier: ' + json.loads(response.text)['identifier']
            return {"status_code": 201, "message": message}

        elif response.status_code == 400:
            sys.stderr.write('Bad Request: Error 400. Event title: ' + json.loads(data[0])[0]['fields'][0]['value'])
            sys.stderr.write('Please check their options and try again, if persists, call the administrator.')
            sys.stderr.write('Details of the error: ' + response.content.decode("utf-8"))
            message = 'Bad Request: Error 400. Event title: ' + json.loads(data[0])[0]['fields'][0]['value']
            return {"status_code": 400, "message": message}
            
            if  response.content.decode("utf-8").lower() == 'Unable to parse device'.lower():
                print('Hint: This error could be caused by the naming setup of the capture agent' + '\n')
                message = 'Unable to parse capture agent name, call the administrator.'
                return {"status_code": 400, "message": message}

        elif response.status_code == 409:
            #Convert times to berlin timezone for the message:
            
            dateTimeStart = dt.datetime.strptime(json.loads(data[3])['start'][:-1], '%Y-%m-%dT%H:%M:%S')
            dateTimeStart = pytz.utc.localize(dateTimeStart)
            local_start = dateTimeStart.astimezone(pytz.timezone(args.timezone))
            local_start_str = local_start.strftime('%Y-%m-%d %H:%M:%S')

            dateTimeEnd = dt.datetime.strptime(json.loads(data[3])['end'][:-1], '%Y-%m-%dT%H:%M:%S')
            dateTimeEnd = pytz.utc.localize(dateTimeEnd)
            local_end = dateTimeEnd.astimezone(pytz.timezone(args.timezone))
            local_end_str = local_end.strftime('%Y-%m-%d %H:%M:%S')




            sys.stderr.write('Scheduling conflict: Error 409. Event title: ' + json.loads(data[0])[0]['fields'][0]['value'] + '\n')
            sys.stderr.write('There is a conflict with other event scheduled between ' + json.loads(data[3])['start'] + ' UTC and \
' + json.loads(data[3])['end'] + ' UTC in the same capture agent, reschedule this event or modify the existing one. \n' )
            message = 'There is a conflict with other event scheduled between ' + local_start_str + ' and ' + local_end_str + ' in the same capture agent, reschedule this event or modify the existing one.'
            return {"status_code": 409, "message": message}


