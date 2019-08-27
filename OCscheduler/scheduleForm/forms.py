from django import forms
from .xml_scheduler import getAgentID
from django.conf import settings

def agentToChoices(oc_url, oc_user, oc_password):
    agentList = []
    agentListJson = getAgentID(oc_url, oc_user, oc_password)
    for agent in agentListJson:
        agentList.append(agent["agent_id"])
    choices = list(zip(agentList, agentList))
    choices.insert(0,("None",'No force agent'))
    return choices
    
class SchedulerForm(forms.Form):
    xmlFile = forms.FileField(label='XML File')
    seriesID = forms.CharField(label='Series-ID', max_length=36)
    
    

    # WorkflowOptions
    NormAudio = forms.BooleanField(label='Normalize Audio', 
                                    initial=True, 
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    PublishToCMS = forms.BooleanField(label='Publish to CMS', 
                                        initial=False,
                                        required=False,
                                        widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    EnableDownload = forms.BooleanField(label='Enable Download',
                                        initial=False,
                                        required=False,
                                        widget=forms.CheckboxInput(attrs={'class':'element checkbox'})) 
    EnableAnnotation = forms.BooleanField(label='Enable Annotation',
                                            initial=False,
                                            required=False,
                                            widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    AutoPublish = forms.BooleanField(label='Autopublish',
                                    initial=False,
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    

   

    #Capture Agent Options (Only Galicaster)
    noCamera = forms.BooleanField(label='Don\'t record the camera',
                                    initial=False,
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    noBeamer = forms.BooleanField(label='Don\'t record the Beamer/Presentation',
                                    initial=False,
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    noAudio = forms.BooleanField(label='Don\'t record Audio',
                                    initial=False,
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))

    #Force capture Agent
    #forceCA = forms.ChoiceField(label='Force capture Agent', required=False, choices=[(None, 'No force agent'),('agent_1', 'agent_1'), ('agent_2','agent_2')])
    
    Track4K = forms.BooleanField(label='Track 4K',
                                initial=False,
                                required=False,
                                widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    Live = forms.BooleanField(label='Live streaming',
                                initial=False,
                                required=False,
                                widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    forceCA = forms.ChoiceField(label='Force capture Agent', required=False, choices=agentToChoices(settings.OPENCAST_URL, settings.OPENCAST_USER, settings.OPENCAST_PASSWD))

    #CreateSBS = forms.BooleanField(label='Create Side-by-Side video', initial=False, required=False)

    xmlFile.group = 'Inputs'
    seriesID.group = 'Inputs'

    NormAudio.group = 'Workflow Options'
    PublishToCMS.group = 'Workflow Options'
    EnableDownload.group = 'Workflow Options'
    EnableAnnotation.group = 'Workflow Options'
    AutoPublish.group = 'Workflow Options'

    noCamera.group = 'Galicaster Options'
    noBeamer.group = 'Galicaster Options'
    noAudio.group = 'Galicaster Options'
    
    Live.group = 'Other Options'
    Track4K.group = 'Other Options' 
    forceCA.group = 'Other Options'
