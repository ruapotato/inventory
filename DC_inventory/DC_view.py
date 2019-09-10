#!/usr/bin/python3
#GPL3
#By: David Hamner
#DC inventory
#Copyright (C) 2019

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.


#import curses
#import curses.textpad
import socket
import sys
import os
import shutil
import time
from datetime import datetime


#from functools import wraps
from flask import Flask, request, Response
#app = Flask(__name__)
from . import DC_inventory
from . env_auth import *
from . configs import *
from . html import *

scriptPath = os.path.dirname(os.path.realpath(__file__))
#change scriptPath to be the main folder/up one dir
scriptPath = scriptPath.split('DC_inventory')[0]

configFiles = scriptPath + "/configs/"
htmlFile = scriptPath + "/index.html"

LabSpace = {}
colorMap = {}
HWTypes = {}
#HWTypes[''] = 2



powerOffColor = "#cc2900"
InfrastructureColor = "#8e13c6"


USER_COLORS = ['0DFFC6','0FFF27','ffffff','ffff00']
#only used if USER_COLORS: is missing from config
colorIndex = 0
USED_COLORS = {}
users = {}
categorys = []

hardware = ""
project = ""
owner = ""
IPMI_WORKING = {}
IPMI_BROKEN = {}
ipmiConfigs = {}
ipmiWaitTime = 60
#tests run on chassis status
IPMI_should_be_false = ['Power Overload', 'Main Power Fault', 'Power Control Fault', 'Drive Fault', 'Cooling/Fan Fault']

HWTypes,LabSpace,colorMap,USER_COLORS,users,categorys = loadEnv()


@DC_inventory.route("/")
def nonAdminRedirect():
    return '<meta http-equiv="refresh" content="0; URL=\'/index.html\' "/>'
@DC_inventory.route("/admin/")
def adminRedirect():
    return '<meta http-equiv="refresh" content="0; URL=\'/admin/index.html\' "/>'

@DC_inventory.route("/index.html")
def nonAdmin():
    return createHtml(admin=False)

@DC_inventory.route("/<lab>/index.html")
def nonAdmin_filter(lab):
    return createHtml(admin=False, filterLab=lab)

@DC_inventory.route("/admin/index.html")
@requires_auth
def adminIndex():
    return createHtml()

@DC_inventory.route("/admin/<lab>/index.html")
@requires_auth
def adminIndex_filter(lab):
    return createHtml(filterLab=lab)


@DC_inventory.route('/admin/scan/<lab>/<configPath>/<newConfig>/<nextToLoad>/<scroll>')
@requires_auth
def scan(lab,configPath,newConfig,nextToLoad,scroll):
    rack = ""
    serverRoom = ""
    sn = ""
    Hardware = ""
    rackU = ""
    nextSN = False #(Only used if sn=na)
    if lab == "all":
        lab = ""


    #replace ~~ with /
    newConfig = newConfig.replace("~~", "/")

    data = loadConfigFromString(newConfig)
    print(data)
    rack = data['rack']
    serverRoom = data['serverRoom']
    sn = data['sn']
    Hardware = data['Hardware']
    rackU = data['rackU']

    #remove color=none
    if data['color'] == 'none':
        newConfig = newConfig.replace('color=none', '')
        #remove empty lines
        newConfig = newConfig.replace('\n\n', '\n')
    if sn.lower() == "na":
        oldSN = sn
        sn = f"{serverRoom}.{rack}.{rackU}".replace(' ', '')
        #update newConfig with SN
        newConfig = newConfig.replace(oldSN + "\n", sn + "\n")
        configPath = configPath.replace(oldSN, sn)
        nextSN = True
    uSize = int(HWTypes[Hardware][0])
    #remove old config file:
    for configName in serverWithSN(sn):
        os.remove(configName)
    os.makedirs(f'{scriptPath}/configs/{serverRoom}/{rack}/', exist_ok=True)
    fullPath = f'{scriptPath}/configs/{serverRoom}/{rack}/{configPath}'
    #WOR$KING


    #write new config
    with open(fullPath, 'w') as fh:
        fh.write(newConfig)

    #debug("FullPath: " + fullPath)
    #return newConfig
    #write newConfig to configPath

    #find next server space by U
    if nextToLoad == "up":
        nextLoadU = int(rackU) + int(uSize)
    elif nextToLoad == "down":
        nextLoadU = int(rackU) - int(uSize)
    #load by U
    elif nextToLoad.isdigit():
        nextLoadU = nextToLoad
    else:
        return createHtml(scroll=scroll, filterLab=lab)
    #debug("UPNext: " + str(scroll))
    if not nextSN: #we don't know the next SN aka: na
        return createHtml(loadU=nextLoadU, loadLab=serverRoom, loadRack=rack, lastRack=data, scroll=scroll, filterLab=lab)
    else:
        return createHtml(loadU=nextLoadU, loadLab=serverRoom, loadRack=rack, lastRack=data, scroll=scroll, snNA=True, filterLab=lab)



@DC_inventory.route('/admin/delete/<filterLab>/<sn>/<scroll>')
@requires_auth
def deleteServer(filterLab, sn, scroll):
    for configName in serverWithSN(sn):
        os.remove(configName)
    return createHtml(scroll=scroll, filterLab=filterLab)

@DC_inventory.route('/configs/<filterLab>/<lab>/<rack>/<configFile>')
@requires_auth
def editRack(filterLab,lab,rack,configFile):
    if filterLab == 'all':
        filterLab = ''
    pathName = f'{scriptPath}/configs/{lab}/{rack}/'
    if not os.path.exists(pathName):
        pass #TODO

    allData = readConfigFile(pathName + configFile)
    #debug("YOYO:" + str(allData))
    return preLoadEditBox(allData, filterLab=filterLab)





