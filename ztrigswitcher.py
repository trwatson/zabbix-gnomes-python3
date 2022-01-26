#!/usr/bin/env python
#
# import needed modules.
# pyzabbix is needed, see https://github.com/lukecyca/pyzabbix
#
import argparse
import configparser
import os
import os.path
import sys
import distutils.util
from pyzabbix import ZabbixAPI

# define config helper function
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print(("exception on %s!" % option))
            dict1[option] = None
    return dict1


# set default vars
defconf = os.getenv("HOME") + "/.zbx.conf"
username = ""
password = ""
api = ""
noverify = ""

# Define commandline arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description='Switches the host inventory mode for the specified host(s) or hostgroup(s). The default setting is to switch to "automatic" mode.', epilog="""
This program can use .ini style configuration files to retrieve the needed API connection information.
To use this type of storage, create a conf file (the default is $HOME/.zbx.conf) that contains at least the [Zabbix API] section and any of the other parameters:
       
 [Zabbix API]
 username=johndoe
 password=verysecretpassword
 api=https://zabbix.mycompany.com/path/to/zabbix/frontend/
 no_verify=true

""")

group = parser.add_mutually_exclusive_group(required=True)
parser.add_argument('triggerid', help='Numeric trigger ID to change status on')
parser.add_argument('-u', '--username', help='User for the Zabbix api')
parser.add_argument('-p', '--password', help='Password for the Zabbix api user')
parser.add_argument('-a', '--api', help='Zabbix API URL')
parser.add_argument('--no-verify', help='Disables certificate validation when nventory_mode using a secure connection',action='store_true') 
parser.add_argument('-c','--config', help='Config file location (defaults to $HOME/.zbx.conf)')
group.add_argument('-E', '--enable', help='Set trigger to enabled', action='store_true')
group.add_argument('-D', '--disable',help='Set trigger to disabled', action='store_true')
args = parser.parse_args()

# load config module
Config = configparser.ConfigParser()
Config

# if configuration argument is set, test the config file
if args.config:
 if os.path.isfile(args.config) and os.access(args.config, os.R_OK):
  Config.read(args.config)

# if not set, try default config file
else:
 if os.path.isfile(defconf) and os.access(defconf, os.R_OK):
  Config.read(defconf)

# try to load available settings from config file
try:
 username=ConfigSectionMap("Zabbix API")['username']
 password=ConfigSectionMap("Zabbix API")['password']
 api=ConfigSectionMap("Zabbix API")['api']
 noverify=bool(distutils.util.strtobool(ConfigSectionMap("Zabbix API")["no_verify"]))
except:
 pass

# override settings if they are provided as arguments
if args.username:
 username = args.username

if args.password:
 password = args.password

if args.api:
 api = args.api

if args.no_verify:
 noverify = args.no_verify

# test for needed params
if not username:
 sys.exit("Error: API User not set")

if not password:
 sys.exit("Error: API Password not set")
 
if not api:
 sys.exit("Error: API URL is not set")

# Setup Zabbix API connection
zapi = ZabbixAPI(api)

if noverify is True:
 zapi.session.verify = False

# Login to the Zabbix API
zapi.login(username, password)

##################################
# Start actual API logic
##################################


if not args.triggerid:
   sys.exit("Error: Triggerid not found")

if args.enable:
   status=int('0')
elif args.disable:
   status=int('1')
else:
   sys.exit("Error: Trigger status not provided")

trigger=zapi.trigger.get(filter={'triggerid':args.triggerid},output='triggerid')

if trigger:
   result=zapi.trigger.update(triggerid=args.triggerid, status=status)
   check=zapi.trigger.get(filter={'triggerid':args.triggerid}, output=['description','status'], expandDescription=1)
   if check[0]['status'] == '0':
      mode="Enabled"
   elif check[0]['status'] == '1':
      mode="Disabled"
   else:
      sys.exit("Error: Something went wrong!")
   print((format(mode) + " : " + format(check[0]['description']))) 

else:
   sys.exit("Error: Trigger not found")


#   sys.exit("Error: No trigger id provided.")


#  try:
#  # Apply the linkage
#   result=zapi.host.massupdate(hosts=hlookup,inventory_mode=invm)
#  except:
#   sys.exit("Error: Something went wrong while performing the update")
# 
#if args.extended:
#  hosts=zapi.host.get(output='extend',hostids=result['hostids'])
#  hostnames=""
#  for host in range(len(hosts)):
#      if not hostnames:
#        hostnames = str(hosts[host]['host'])
#      else:
#        hostnames = hostnames + ", " + str(hosts[host]['host'])
#  print("Inventory mode switched to \"" + args.mode + "\" on: " + hostnames)
#  
# And we're done...
