# Item Catalog Project - Linux Server Configuration

A web application where you can create  a list of singers and add to them their songs. users have the ability to post, edit, and delete their own songs only. it uses third party authentication,deployed in a linux distribution. 


* IP: 18.222.182.250
* SSH port:2200
* URL : http://ec2-18-222-182-250.us-east-2.compute.amazonaws.com/

## ssh
ssh -i  PRIVATE-KEY -p 2200 grader@18.222.182.250

## required installations:

1- Apache2 with mod_wsgi module

2- Python 3

3- UFW for firewall


## Third party apps used:

1- OAuth

2- Flask



# Configurations

## apache 

```
<VirtualHost *:80>
    ServerName 18.222.182.250
    ServerAlias ec2-18-222-182-250.us-east-2.compute.amazonaws.com
    ServerAdmin admin@18.222.182.250
    WSGIScriptAlias / /var/www/catalog/catalog.wsgi
    <Directory /var/www/catalog/catalog/>
        Order allow,deny
        Allow from all
    </Directory>
    Alias /static /var/www/catalog/catalog/static
    <Directory /var/www/catalog/catalog/static/>
        Order allow,deny
        Allow from all
    </Directory>
    ErrorLog ${APACHE_LOG_DIR}/error.log
    LogLevel warn
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```
  
##WSGI 

```
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,'/var/www/catalog/catalog')
sys.path.insert(1,"/var/www/catalog/")
from __init__ import app as application
application.secret_key ='ADD SECRET KEY HERE'
```



