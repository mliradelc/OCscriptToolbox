
from .forms import SchedulerForm
from .xml_scheduler import XmlGP, args, get_acl, payload, post, getAgentID
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
import django.utils
import json
import OCscheduler.properties as properties

def setKey(request ,key):
    try:
        if request.POST.__getitem__(key) == 'on':
            return True
        else:
            return False
    except django.utils.datastructures.MultiValueDictKeyError:
        return False

def home(request):
    return render(request, 'schedule/home.html')

def scheduler(request):
    query = args()
    if request.method == 'POST':
        filled_form = SchedulerForm(request.POST, request.FILES)
        if request.FILES['xmlFile'].content_type != 'text/xml':
            # If the file is not type 'text/xml'
            messages.info(request,'Error: The file is not a XML file, the series was not scheduled')
            new_form = SchedulerForm()
            return render(request, 'scheduler.html',{'SchedulerForm':new_form})

        # If the form was succesfully validated
        if filled_form.is_valid():
                   
            # Get the XML file
            XMLfile = request.FILES['xmlFile']
            parsedXml = XmlGP(XMLfile)

            # Opencast server and capture agent properties
            query.username = properties.OPENCAST_USER
            query.password = properties.OPENCAST_PASSWD
            query.serverUrl = properties.OPENCAST_URL
            query.timezone = properties.MESSAGES_TIMEZONE
            query.dictCA = properties.CAPTURE_AGENT_DICT

            # Form properties
            query.seriesID = request.POST.__getitem__('seriesID')
            query.forceCA = request.POST.__getitem__('forceCA')
            query.normalizeaudio = setKey(request, 'NormAudio')
            #query.publishtocms = setKey(request, 'PublishToCMS')
            query.publishtocms = True
            query.enabledownload = setKey(request, 'EnableDownload')
            #query.createsbs = setKey(request, 'CreateSBS')
            query.createsbs = False
            query.enableannotation = setKey(request, 'EnableAnnotation')
            query.autopublish = setKey(request, 'AutoPublish')
            query.publishlive = setKey(request, 'Live')
            query.track4k = setKey(request, 'Track4K')
            query.nocamera = setKey(request, 'noCamera')
            query.nobeamer = setKey(request, 'noBeamer')
            query.noaudio = setKey(request, 'noAudio')
            query.test = False
            
            acl = get_acl(query.serverUrl, query.username, query.password, query.seriesID)
            agents = getAgentID(query.serverUrl, query.username, query.password)
            
            if acl["code"] == 0:
                flag_not_good = 0
                for row in parsedXml:
                    data = payload(row, query, acl["json"], agents)
                    
                    #If there is no capture agent
                    try:
                        if data["code"] != 0:
                            if data ["code"] == 1:
                                messages.error(request, data["message"])
                            else:
                                messages.error(request, "Capture agent error, contact ***REMOVED***istrator")
                        new_form = SchedulerForm()
                        return render(request, 'scheduler.html', {'SchedulerForm':new_form})
                    except TypeError:
                        pass
                    
                    
                    #Send the data to opencast
                    send = post(query, data)

                    #All Ok
                    if send["status_code"] == 201:
                        messages.info(request, send["message"])
                    
                    #Schedule conflict
                    if send["status_code"] == 409:
                        messages.warning(request, send["message"])
                        flag_not_good = 1
                    
                    #Bad request
                    if send["status_code"] == 400:
                        messages.error(request, send["message"])
                        flag_not_good = 1

                    
                if flag_not_good == 0:
                    messages.success(request, 'The series %s was succesfully scheduled in the system' %(filled_form.cleaned_data['seriesID']))
                else:
                    messages.error(request, 'Some or all events of %s had not been scheduled, please check if there is a schedule conflict' %(filled_form.cleaned_data['seriesID']))
            else:
                messages.error(request, acl["message"]) 
        else:
            # If there is an error with the form
            messages.error(request,'There was an error, the series was not scheduled')
              
        new_form = SchedulerForm()
        return render(request, 'scheduler.html',{'SchedulerForm':new_form})
    else:
        form = SchedulerForm()
        return render(request, 'scheduler.html', {'SchedulerForm':form})


