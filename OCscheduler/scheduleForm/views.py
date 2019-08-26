from django.shortcuts import render
from .forms import SchedulerForm
from .xml_scheduler import XmlGP, args, get_acl, payload, post, getAgentID
from django.conf import settings
import django.utils

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
            # If the file is the type 'text/xml'
            note = 'Error: The file is not a XML file, the series was not scheduled'
            new_form = SchedulerForm()
            return render(request, 'scheduler.html',{'SchedulerForm':new_form, 'note':note})

        if filled_form.is_valid():
            # If the form was succesfully validated
            XMLfile = request.FILES['xmlFile']
            parsedXml = XmlGP(XMLfile)

            #data from the settings
            query.username = settings.OPENCAST_USER
            query.password = settings.OPENCAST_PASSWD
            query.serverUrl = settings.OPENCAST_URL

            query.seriesID = request.POST.__getitem__('seriesID')
            query.forceCA = request.POST.__getitem__('forceCA')


            query.normalizeaudio = setKey(request, 'NormAudio')
            query.publishtocms = setKey(request, 'PublishToCMS')
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
            for row in parsedXml:
                data = payload(row, query, acl, agents)
                post(query, data)

            note = 'The series %s was succesfully scheduled in the system' %(filled_form.cleaned_data['seriesID'])
        else:
            # If there is an error with the form
            note = 'There was an error, the series was not scheduled'
        new_form = SchedulerForm()


        return render(request, 'scheduler.html',{'SchedulerForm':new_form, 'note':note})
    else:
        form = SchedulerForm()
        return render(request, 'scheduler.html', {'SchedulerForm':form})


