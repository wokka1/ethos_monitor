#!/usr/bin/python3

# version 1.0.1

# ethos monitoring script
# this is designed to run from your crontab, it will check your rig(s) stat page once per execution
# it currently supports Cisco Spark and iOS Prowl notifications
#
# by default, nothing is enabled, so it will print to the command line
# the ethos_hostname has to be set or you will get an error
#
# written by wokka - 3 Feb 2018
# no worranty or support comes with this, use it as you want
# licensed under GPLv3
# change the variables accordingly

import json 
import requests
import datetime
import logging, sys
import apprise
apobj = apprise.Apprise()

# =-=-=-=-=-=-=-==-
# Variables
# =-=-=-=-=-=-=-==-

# those panel hostname - this must be set in order to poll your rig(s)
ethos_hostname = "change me"

# temperature alert, set this to what you want to be alerted, if it's higher than this variable, you will get an alert
alert_temp = 70

# fan rpm alert
alert_rpm = 2000

# hash rate
alert_hash = 20

# if you need it to skip a rig on checks, change this, otherwise you can ignore
skip_rig = "69fff4"

# this enables debugs if you want to get some variables printed at command line
debug = "false"

# Cisco Spark notification variables.  ciscospark.com for more details, look under development documentation
bearer = "change me"
room = "change me"
spark_enable = "false"

# Apple iOS prowl notifications, change the api key if you are going to use this and enable
apobj.add('prowl://change me')
prowl_enable = "false"

# =-=-=-=-=-=-=-==-
# change nothing below here
# =-=-=-=-=-=-=-==-
bot_email = "whiskey@sparkbot.io"
bot_name = "Whiskey"
msg = ""

# [Prowl](https://github.com/caronc/apprise/wiki/Notify_prowl) | prowl:// | (TCP) 443 | prowl://apikey
# prowl://apikey/providerkey

#msg = "test : " + ethos_hostname
#apobj.notify(title='test',body=msg)

if ethos_hostname == "change me":
    print ("please configure the ethos_hostname in the python script to enable monitoring, read the comments for additional info")
    raise SystemExit(0)

localtime = datetime.datetime.now()
header = {'Content-Type': 'application/json; charset=utf-8'}
uri = 'http://' + ethos_hostname + '.ethosdistro.com/?json=yes'
resp = requests.get(uri, headers=header)
a = json.dumps(resp.json())
b = json.loads(a) # decode JSON format

def setHeaders():         
    accessToken_hdr = 'Bearer ' + bearer
    spark_header = {'Authorization': accessToken_hdr, 'Content-Type': 'application/json; charset=utf-8'}
    return spark_header

def sendSparkGET(url):
    header = setHeaders()
    contents = requests.get(url, headers=header)
    return contents.json()
   
def sendSparkPOST(url, msg):
    header = setHeaders()
    contents = requests.post(url, data=json.dumps(msg), headers=header) 
    return contents.json

rigs = list(b["rigs"].keys())
for rig_idx, rigname in enumerate(rigs):
    if rigname == skip_rig:
        continue
    rig_hash = b["rigs"][rigname]["hash"]
    rack_loc = b["rigs"][rigname]["rack_loc"]
    gpu_temp_str = b["rigs"][rigname]["temp"]
    gpu_temp = gpu_temp_str.split() 
    miner_hashes_str = b["rigs"][rigname]["miner_hashes"]
    miner_hashes = miner_hashes_str.split() 
    fanrpm_str = b["rigs"][rigname]["fanrpm"]
    fanrpm = fanrpm_str.split() 
    core_str = b["rigs"][rigname]["core"]
    core = core_str.split() 
    mem_str = b["rigs"][rigname]["mem"]
    mem = mem_str.split()
    idx = 0
    fidx = 0
    hidx = 0

    if debug == "true":
        print ("rigname " + rigname)
        print ("temps " + str(gpu_temp))
        print ("hashes " + str(miner_hashes))
        print ("rpm " + str(fanrpm))
        print ("core " + str(core))
        print ("mem " + str(mem))
        print ()
    for idx, temp in enumerate(gpu_temp):
        if float(temp) > alert_temp:
            msg = ("Rig : " + rack_loc + " - " + rigs[rig_idx] + " - GPU " + str(idx) + " : is at " + str(temp) + "c - fan : " + fanrpm[idx] + " RPM and settings are Memory Clock " + mem[idx] + "MHz, Core Clock at " + core[idx] + "MHz")
            if spark_enable == "true":
                sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": room, "text": msg})
            if prowl_enable == "true":
                apobj.notify(title='Rig Problems',body=msg)
            else:
               print (msg)

    for fidx, rpm in enumerate(fanrpm):
        if float(rpm) < alert_rpm:
            msg =  ("Rig : " + rack_loc + " - " + rigs[rig_idx] + " - GPU " + str(fidx) + " : is at " + fanrpm[fidx] + " RPM - temp : " + str(temp) + "c and settings are Memory Clock " + mem[fidx] + "MHz, Core Clock at " + core[fidx] + "MHz")
            if spark_enable == "true":
                sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": room, "text": msg})
            if prowl_enable == "true":
                apobj.notify(title='Rig Problems',body=msg)
            else:
               print (msg)

    for hidx, hash in enumerate(miner_hashes):
        if float(hash) < alert_hash:
            msg = ("Rig : " + rack_loc + " - " + rigs[rig_idx] + " - GPU " + str(hidx) + " : is at " + hash + " MH/is - temp : " + str(temp) + "c and settings are Memory Clock " + mem[hidx] + "MHz, Core Clock at " + core[hidx] + "MHz")
            if spark_enable == "true":
                sendSparkPOST("https://api.ciscospark.com/v1/messages", {"roomId": room, "text": msg})
            if prowl_enable == "true":
                apobj.notify(title='Rig Problems',body=msg)
            else:
               print (msg)

