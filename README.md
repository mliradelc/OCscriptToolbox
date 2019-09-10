# OCscriptToolbox
A Django-based framework that contains a series of scripts as web applications

>At this moment it only contains one application, OC Scheduler, more tools will come later.

![sample demo](docs/resources/OCScheduler_example_longV2.gif)

## Installation

Like any Django application is needed a Web Server Gateway Interface (WSGI) server to work. In my case I developed OCscriptToolboox using [mod_wsgi](http://www.modwsgi.org/).


If you only want to develop or try also is possible to run it using the [`runserver` command](https://docs.djangoproject.com/en/2.2/ref/django-***REMOVED***/#runserver) (After installing the virtual environment)


### Prerequisites

OCscriptToolbox was designed under Python 3.6, to work is required that the WSGI server supports Python 3.

For installation of mod_wsgi in Centos 7, please look the [appendix](#Appendix).

### Configure Webserver (Apache)

> This instructions use the standard folders for apache in Centos 7, similar installation is for the other flavors of linux.

1. Clone this repository in `/var/www/`
1. move the file `config_files/apache/oc-toolbox.conf` to the folder `/etc/httpd/conf.d/` or add the contents to the end of the apache config file.

### Configure the Webapp

1. In the root folder of the app (Ex: `/var/www/OCscriptToolbox/`) create a new virtual environment called "env"
    
    `$ virualenv env --no-site-packages`

1. Activate the virtual environment.
    
    `$ source env/bin/activate`

1. Now that the Venv is activated, install the dependencies with PIP.

    `(env)$ pip install -r requirements.txt`

1. Collect the Static files
    ```bash
    (env)$ cd /var/www/OCscriptToolbox
    (env)$ python3 manage.py collectstatic
    ```
1. Set the [Allowed hosts](https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts) in the app settings located in `/var/www/OCscriptToolbox/OCscheduler/settings.py`

1. Deactivate the virtual environment.

    `(env)$ deactivate`

### Configure credentials and capture agent dictionary

In the file `OCscheduler/properties.py`, 
* Add the credentials. The credentials has to be with a user able to access to the external API of opencast.

* Set the Opencast server address

* Set the capture agent dictionary, this parameter is very important because allows to map the room code from the KLIPS system with the list of names registered in Opencast.

The names of each option are the same that are set on the user options in the Workflows.

### Configure webform

The webform is actually configured for a custom made options for the University of cologne. If you want to use with your own parameters, you need to modify the options names in:

* [forms.py](OCscheduler/scheduleForm/forms.py)
* [views.py](OCscheduler/scheduleForm/views.py)
* [xml_scheduler.py](OCscheduler/scheduleForm/xml_scheduler.py)

The option names are in the start workflow to start a task in Opencast, also you have to change in the last file the name of the 


### Restart apache and enter to the application

Restart apache using `$ sudo systemctl restart httpd`. After restart enter to the webpage using `<hostname>/oc-toolbox/scheduler` 


# Troubleshooting

## The site shows errors

* Look the apache error log `$ sudo tail /var/log/httpd/error_log` if there is some configuration error

* Enable the [Django debug mode](https://docs.djangoproject.com/en/2.2/ref/settings/#debug), with this you can found more easy the error.


# Apendix

## How to install mod WSGI for python 3.x in Centos 7

mod_wsgi, the WSGI server that uses apache, it can be installed directly from the Centos 7 repository, unfortunately, this version is only for Python 2.x and it will not work with applications made for Python 3.x

```console
$ pip3 install mod_wsgi
$ sudo rm /etc/httpd/conf.modules.d/10-wsgi.conf
$ sudo cp /usr/local/bin/mod_wsgi-express /usr/bin/
$ sudo mod_wsgi-express install-module > /etc/httpd/conf.modules.d/02-wsgi.conf
```



