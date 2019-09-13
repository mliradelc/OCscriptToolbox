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
# Forms generator file                                                          #
# Author: Maximiliano Lira Del Canto                                            #
# Date: September 2019                                                          #
#                                                                               #
#################################################################################


from django import forms
from .xml_scheduler import getAgentID
from django.conf import settings
import OCscheduler.properties as properties

#Generate the available agent list to choose in the force CA
def agentToChoices(oc_url, oc_user, oc_password):
    agentList = []
    agentListJson = getAgentID(oc_url, oc_user, oc_password)
    for agent in agentListJson:
        agentList.append(agent["agent_id"])
    choices = list(zip(agentList, agentList))
    choices.insert(0,("None",'No force agent'))
    return choices
    
class SchedulerForm(forms.Form):
    #Input options
    xmlFile = forms.FileField(label='XML File',
                                help_text='XML file from Klips System')
    seriesID = forms.CharField(label='Series-ID', max_length=36,
                                help_text='The ID found in series properties in opencast')
    
    

    # WorkflowOptions
    NormAudio = forms.BooleanField(label='Normalize Audio', 
                                    initial=True, 
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
                                    help_text='Normalize the differences between voices')
    # PublishToCMS = forms.BooleanField(label='Publish to CMS', 
    #                                     initial=False,
    #                                     required=False,
    #                                     widget=forms.CheckboxInput(attrs={'class':'element checkbox'}))
    EnableDownload = forms.BooleanField(label='Enable Download',
                                        initial=False,
                                        required=False,
                                        widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
                                        help_text='Allows to download the videos') 
    EnableAnnotation = forms.BooleanField(label='Enable Annotation',
                                            initial=False,
                                            required=False,
                                            widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
                                            help_text='Enables the Annotation tool to be used')
    AutoPublish = forms.BooleanField(label='Autopublish',
                                    initial=False,
                                    required=False,
                                    widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
                                    help_text='Publish the event automatically without editing')
    #CreateSBS = forms.BooleanField(label='Create Side-by-Side video',
    #                               initial=False,
    #                               required=False,
    #                               widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
    #                               help_text='Creates a single video with the presenter and the beamer side-by-side')

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


    #Other options    
    Track4K = forms.BooleanField(label='Track 4K',
                                initial=False,
                                required=False,
                                widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
                                help_text='(Only for rooms with 4k cameras) Allows automatic zoom tracking in the video')
    Live = forms.BooleanField(label='Live streaming',
                                initial=False,
                                required=False,
                                widget=forms.CheckboxInput(attrs={'class':'element checkbox'}),
                                help_text='(Only for Extron CA) Streams the event live when is recorded')
    forceCA = forms.ChoiceField(label='Force capture Agent', 
                                required=False, 
                                choices=agentToChoices(properties.OPENCAST_URL, properties.OPENCAST_USER, properties.OPENCAST_PASSWD),
                                help_text='Forces to use another capture Agent (Ex: For special events that will use a mobile CA)')

    

    #Set input groups
    # The input groups are used for grouping the form options for the website render.

    xmlFile.group = 'Inputs'
    seriesID.group = 'Inputs'

    NormAudio.group = 'Workflow Options'
    #PublishToCMS.group = 'Workflow Options'
    EnableDownload.group = 'Workflow Options'
    EnableAnnotation.group = 'Workflow Options'
    AutoPublish.group = 'Workflow Options'
    #CreateSBS.group = 'Workflow Options'

    noCamera.group = 'Galicaster Options'
    noBeamer.group = 'Galicaster Options'
    noAudio.group = 'Galicaster Options'
    
    Live.group = 'Other Options'
    Track4K.group = 'Other Options' 
    forceCA.group = 'Other Options'
