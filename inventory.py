#!/usr/bin/python3
#GPL3
#By: David Hamner
#inventory.py
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
import subprocess
import os
import shutil
import time
import threading
from datetime import datetime

scriptPath = os.path.dirname(os.path.realpath(__file__))
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

from functools import wraps
from flask import Flask, request, Response
app = Flask(__name__)

#Thanks: http://flask.pocoo.org/snippets/8/
def check_auth(username, password):
    global usrers
    """This function is called to check if a username /
    password combination is valid.
    """
    if username in users:
        if users[username] == password:
            return True
    return False

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Login Error!\n', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def nonAdminRedirect():
    return '<meta http-equiv="refresh" content="0; URL=\'/index.html\' "/>'
@app.route("/admin/")
def adminRedirect():
    return '<meta http-equiv="refresh" content="0; URL=\'/admin/index.html\' "/>'

@app.route("/index.html")
def nonAdmin():
    return createHtml(admin=False)

@app.route("/<lab>/index.html")
def nonAdmin_filter(lab):
    return createHtml(admin=False, filterLab=lab)

@app.route("/admin/index.html")
@requires_auth
def adminIndex():
    return createHtml()

@app.route("/admin/<lab>/index.html")
@requires_auth
def adminIndex_filter(lab):
    return createHtml(filterLab=lab)

@app.route('/admin/ipmisetup/<lab>/<rack>/<sn>/<ip>/<user>/<passwd>')
@requires_auth
def ipmiAdd(lab, rack, sn, ip, user, passwd):
    returnHtml = ""
    fullPath = f'{scriptPath}/configs/{lab}/{rack}/{sn}.ipmi'
    fileStuff = f"{ip}:{user}:{passwd}"
    with open(fullPath, 'w') as fh:
        fh.write(fileStuff)
    return(returnHtml)


@app.route('/admin/IPMI/<lab>/<rack>/<sn>')
@requires_auth
def ipmiHtml(lab,rack,sn):
    returnHtml = """
    IP: <input id=ipmiIP></input> <br>
    User: <input id=ipmiUser></input> <br>
    Password: <input id=ipmiPasswd></input> <br>"""
    
    fullPath = f'{scriptPath}/configs/{lab}/{rack}/{sn}.ipmi'
    logName = fullPath[:-5] + ".log"
    
    if os.path.isfile(fullPath):
        if fullPath in IPMI_BROKEN:
            returnHtml = "Error connecting: <br>" + IPMI_BROKEN[fullPath].replace("\\n", "<br>") + "<br>" + returnHtml
        elif fullPath in IPMI_WORKING:
            extraHtml = ""
            if os.path.isfile(logName):
                temps = list(tail(logName))
                temps.reverse()
                for line in temps:
                    line = line.decode('UTF-8').split('|')
                    line = f"Front temp: {line[0]}, Back temp: {line[1]}, Health: {line[2]}, Power: {line[3]}, Date: {line[-1]}"
                    extraHtml = extraHtml + line + "<br>\n"
                extraHtml = "Logs:<br>\n" + extraHtml + "\n"
            returnHtml = "Edit working IPMI..." + "<br>" + returnHtml + extraHtml
        else:
            returnHtml = "Unknown status: " + str(ipmiConfigs) + "<br>" + returnHtml
    else:
        returnHtml = "New Connection<br>" + returnHtml
        
    return(returnHtml)

@app.route('/admin/scan/<lab>/<configPath>/<newConfig>/<nextToLoad>/<scroll>')
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
        newConfig = newConfig.replace(oldSN, sn)
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



@app.route('/admin/delete/<filterLab>/<sn>/<scroll>')
@requires_auth
def deleteServer(filterLab, sn, scroll):
    for configName in serverWithSN(sn):
        os.remove(configName)
    return createHtml(scroll=scroll, filterLab=filterLab)

@app.route('/configs/<filterLab>/<lab>/<rack>/<configFile>')
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


CSS = """
<!--Thanks to www.racktables.org-->
<style>
th.rack {
        font: bold 12px Verdana, sans-serif;
}

.rack {
        font: bold 12px Verdana, sans-serif;
        border: 1px solid black;
        border-top: 0px solid black;
        border-right: 0px solid black;
        padding-right: 15px;
        text-align: center;
        float:left;
}

.rack th {
        border-top: 1px solid black;
        border-right: 1px solid black;
}

.rack td {
        border-top: 1px solid black;
        border-right: 1px solid black;
  max-width: 100px;
  overflow: hidden;
  white-space: nowrap;
}

.rack a {




        font: bold 10px Verdana, sans-serif;
        color: #000;
        text-decoration: none;
}

.rack a:hover {
        text-decoration: underline;
}

.rackspace {
}

.rackspace img {
        border: 0;
        display: inline;
        margin: 0;
        padding: 0;
}

.rackspace h2 {
        font: bold 25px Verdana, sans-serif;
}

.rackspace h3 {
        font: bold 20px Verdana, sans-serif;
}

.rackspace a {
        color: #000;
        text-decoration: none;
}

.rackspace a:hover {
        color: #000;
        text-decoration: underline;
}


/*common rack item attributes*/
.atom {
        text-align: center;
        font: bold 10px Verdana, sans-serif;
}
.state_F   { background-color: #8fbfbf; }
.state_A   { background-color: #bfbfbf; }
.state_U   { background-color: #bf8f8f; }
.state_T   { background-color: #408080; }
.state_Th  { background-color: #80ffff; }
.state_Tw  { background-color: #804040; }
.state_Thw { background-color: #ff8080; }
.state_Thw { background-color: #ff8080; }

/* highlighting for drag selection */
.atom.ui-selecting {
        background-color: #E2D087 !important;
}

/* link with single image as body */
a.img-link {
        vertical-align: bottom;
}

/* text label with rackcode (object-rackspace tab) */
.filter-text {
        font-family: "Courier New",Courier,monospace;
}

/* taken from: https://www.w3schools.com/howto/howto_js_filter_table.asp */
* {
  box-sizing: border-box;
}

#filterInput {
  background-position: 10px 10px;
  background-repeat: no-repeat;
  width: 100%;
  font-size: 16px;
  padding: 12px 20px 12px 40px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}

#filterTable {
  border-collapse: collapse;
  width: 100%;
  border: 1px solid #ddd;
  font-size: 18px;
}

#filterTable th, #filterTable td {
  text-align: left;
  padding: 12px;
  word-wrap: break-word;         /* All browsers since IE 5.5+ */
  overflow-wrap: break-word;
}

#filterTable tr {
  border-bottom: 1px solid #ddd;
}

#filterTable tr.header, #filterTable tr:hover {
  background-color: #f1f1f1;
}

.storage {
  font-family: arial, sans-serif;
  border: 1px solid #dddddd;
}

.storage th {
  text-align: left;
  padding: 8px;
  border: 1px solid #000000;
}
#editServer {
  position: fixed;
  top: 70px;
  left: 2%;
  width: 18%;
  height: 100%;
  background-color: #EEEEEF;
}
#links {
  position: fixed;
  top: 5px;
  float: right;
  right: 0;
  height: auto%;
  background-color: #AAAAAA;
  text-align: right;
  padding: 5px;
}
#updateDiv {
  position: fixed;
  top: 30px;
  left: 30px;
  width: 65px;
  height: auto%;
  background-color: #999999;
  padding: 5px;
}
#updateIPMI {
  position: fixed;
  left: 10%;
  width: 120px;
  height: auto%;
  background-color: #9999ff;
  padding: 5px;
}
#ipmiDiv {
  position: fixed;
  top: 30px;
  left: 95px;
  width: 50px;
  height: auto%;
  background-color: #9999FF;
  padding: 5px;
}
#deleteDiv {
  position: fixed;
  top: 30px;
  left: 140px;
  width: 62px;
  height: auto%;
  background-color: #FF1111;
  padding: 5px;
}
#colorDiv {
  position: fixed;
  top: 30px;
  left: 202px;
  width: 121px;
  height: auto%;
  background-image: linear-gradient(to right, green, yellow, orange,red);
  padding: 5px;
}
.tooltip {
  display: inline-block;
  border-bottom: 1px dotted black;
  color: black;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: auto;
  background-color: black;
  color: #fff;
  text-align: left;
  border-radius: 6px;
  padding: 5px 0;

  /* Position the tooltip */
  position: absolute;
  z-index: 1;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
}

.blinking{
    animation:blinkingText 0.8s infinite;
}
@keyframes blinkingText{
    0%{     color: #000;    }
    50%{    color: red; }
    100%{   color: #000;    }
}
/* The Legend (background) */
.legend {
  display: none; /* Hidden by default */
  position: fixed; /* Stay in place */
  z-index: 1; /* Sit on top */
  padding-top: 100px; /* Location of the box */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgb(0,0,0); /* Fallback color */
  background-color: rgba(0,0,0,0.4); /* Black w/ opacity */
}
}
/* Legend Content */
.legend-content {
  background-color: #fefefe;
  margin: auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
}

.ipmiPopup {
  display: none; /* Hidden by default */
  position: fixed; /* Stay in place */
  z-index: 1; /* Sit on top */
  padding-top: 100px; /* Location of the box */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgb(0,0,0); /* Fallback color */
  background-color: rgba(0,0,0,0.4); /* Black w/ opacity */
}

/* Legend Content */
.ipmi-content {
  background-color: #fefefe;
  margin: auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
  height: 70%;
}
/* The Close Button */
.close {
  color: #aaaaaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
}

.close:hover,
.close:focus {
  color: #000;
  text-decoration: none;
  cursor: pointer;
}

.grid-container {
  display: grid;
  grid-template-columns: auto auto auto;
  background-color: #2196F3;
  padding: 10px;
}

.grid-item {
  background-color: rgba(255, 255, 255, 0.8);
  padding: 20px;
  font: bold 20px Verdana, sans-serif;
  border: 2px solid black;
  border-bottom: 0px;
  text-align: center;
  float:center;
}


</style>
"""

def JS(scroll=0, admin=True, lab=""):
    if lab == "":
        lab = "all"
    
    extraOnLoadJS = ""
    jsColor = ""
    if admin:
        for line in open(scriptPath + '/jscolor.js').readlines():
            jsColor = jsColor + line
        extraOnLoadJS = """
        // Get the ipmi
        var IPMI = document.getElementById('ipmi');

        // Get the button that opens the IPMI
        var btn = document.getElementById("ipmiBtn");

        // Get the <span> element that closes the IPMI
        var span = document.getElementsByClassName("close")[0];

        // When the user clicks the button, open the IPMI
        btn.onclick = function() {
            IPMI.style.display = "block";
            load_IPMI();
        }

        // When the user clicks on <span> (x), close the IPMI
        span.onclick = function() {
            IPMI.style.display = "none";
        }

        // When the user clicks anywhere outside of the IPMI, close it
        window.onclick = function(event) {
            if (event.target == IPMI) {
            IPMI.style.display = "none";
            }
        }
        """

    script = "<script>" + jsColor + """
    window.addEventListener("load", function(){
      // Get the legend
      var legend = document.getElementById('myLegend');

      // Get the button that opens the legend
      var btn = document.getElementById("myBtn");

      // Get the <span> element that closes the legend
      var span = document.getElementsByClassName("close")[0];

      // When the user clicks the button, open the legend
      btn.onclick = function() {
        legend.style.display = "block";
      }

      // When the user clicks on <span> (x), close the legend
      span.onclick = function() {
        legend.style.display = "none";
      }

      // When the user clicks anywhere outside of the legend, close it
      window.onclick = function(event) {
        if (event.target == legend) {
          legend.style.display = "none";
        }
      }
      """+extraOnLoadJS+"""
      //move back to last known position
      window.scrollTo(0, """ + str(scroll) + """);

      try {
        var doc=document.querySelector("#dataObj").contentDocument;
      }
      catch(err) {
          var doc=document
      }
      doc.getElementById('SN').focus();
      doc.getElementById('SN').onkeypress = function(event){
          if (event.keyCode == 13 || event.which == 13){
              updateEdit();
          }
      };
      try {
      document.getElementById(location.hash.slice(1)).scrollIntoView();
      }catch(err) {}

    });
    function filterFunction() {
      var input, filter, table, tr, td, i, txtValue, allText, sections;
      input = document.getElementById("filterInput");
      filter = input.value.toUpperCase();
      table = document.getElementById("filterTable");
      tr = table.getElementsByTagName("tr");
      for (var i = 0; i < tr.length; i++) {
        allText = "";
        sections = tr[i].getElementsByTagName("td");
        for (var e = 0; e < sections.length; e++) {
          td = tr[i].getElementsByTagName("td")[e]
          if (td) {
            allText = allText + td.textContent || td.innerText;
          }
        }

        if (allText) {
          if (allText.toUpperCase().indexOf(filter) > -1) {
            tr[i].style.display = "";
          } else {
            tr[i].style.display = "none";
          }
        }
      }
    }
    function load_IPMI() {
        try {
            var doc=document.querySelector("#dataObj").contentDocument;
        }
        catch(err) {
            var doc=document
        }
        var SN = doc.getElementById('SN').value;
        var serverRoom = doc.getElementById('serverRoom').value;
        var rack = doc.getElementById('rack').value;
        if(SN == "") {
            alert("Enter serial");
            var IPMI = document.getElementById('ipmi');
            IPMI.style.display = "none";
            return;
        }
        var URL = '/admin/IPMI/' + serverRoom + '/' + rack + '/' + SN;
        document.getElementById("ipmi-content").innerHTML='<object id=dataObj2 style="float:left; width: 100%; height: 100%;" type="text/html" data=' + encodeURI(URL) + ' ></object>';
    }
    function load_server(url) {
        document.getElementById("editServer").innerHTML='<object id=dataObj style="float:left; width: 100%; height: 100%;" type="text/html" data=' + encodeURI(url) + ' ></object>';
        document.querySelector('#dataObj').addEventListener('load', function(){

            try {
              var doc=document.querySelector("#dataObj").contentDocument;
            }
            catch(err) {
                var doc=document
            }
            doc.getElementById('SN').focus();
            doc.getElementById('SN').onkeypress = function(event){
                if (event.keyCode == 13 || event.which == 13){
                    updateEdit();
                }
            };
          });
    }

    """
    if not admin:
        return script + " </script>"
    else:
        return script + """
        function showColor() {
          var x = document.getElementById("pickColor");
          if (x.style.display === "none") {
            x.style.display = "block";
          } else {
            x.style.display = "none";
          }
        }
        function deleteServer() {
            try {
              var doc=document.querySelector("#dataObj").contentDocument;
            }
            catch(err) {
              var doc=document
            }
            var SN = doc.getElementById('SN').value;
            if(SN == "") {
              alert("Enter serial");
              return;
            }
            var URL = '/admin/delete/""" + lab + """/' + SN + '/' + window.pageYOffset;
            window.open(URL,"_self");
        }
        function updateIPMI() {
            try {
              var doc=document.querySelector("#dataObj2").contentDocument;
            }
            catch(err) {
              var doc=document;
            }
            try {
              var doc2=document.querySelector("#dataObj").contentDocument;
            }
            catch(err) {
              var doc2=document;
            }
            //call page to write config
            alert('UpateIPMI');
            debugger;
            var user = doc.getElementById('ipmiUser').value;
            var ip = doc.getElementById('ipmiIP').value;
            var passwd = doc.getElementById('ipmiPasswd').value;
            var SN = doc2.getElementById('SN').value;
            var serverRoom = doc2.getElementById('serverRoom').value;
            var rack = doc2.getElementById('rack').value;
            
            var URL = '/admin/ipmisetup/' + serverRoom + '/' + rack + '/' + SN + '/' + ip + '/' + user + '/' + passwd
            document.getElementById("ipmi-content").innerHTML='<object id=dataObj2 style="float:left; width: 100%; height: 100%;" type="text/html" data=' + encodeURI(URL) + ' ></object>';
            
            var IPMI = document.getElementById('ipmi');
            IPMI.style.display = "none";
            
                    
        
        
        var URL = '/admin/IPMI/' 
        
        
        }
        function updateEdit() {
            var path = "";
            try {
              var doc=document.querySelector("#dataObj").contentDocument;
            }
            catch(err) {
              var doc=document
            }
            var serverRoom = doc.getElementById('serverRoom').value;
            var rack = doc.getElementById('rack').value;
            var rackU = doc.getElementById('rackU').value;
            var project = doc.getElementById('project').value;
            var owner = doc.getElementById('owner').value;
            var hardware = doc.getElementById('Hardware').value;
            var notes = doc.getElementById('notes').value;
            var powered = doc.getElementById('powered').value;
            var SN = doc.getElementById('SN').value;
            var BC = doc.getElementById('BC').value;
            var newTicket = doc.getElementById('newTicket').value;
            var color = document.getElementById('pickColor');
            var category = doc.getElementById('categorys').value;

            if (color.style.display === "none")
            {
              color = "none"
            }
            else
            {
              color = color.value;
            }

            //for loop
            var links = "";
            for(var i=0; i < doc.getElementsByName('tickets').length;i++)
            {
              var status = doc.getElementById(doc.getElementsByName('tickets')[i].text).value;
              if(status == "Open") {status = "True";}
              if(status == "Closed") {status = "False";}
              links = links + doc.getElementsByName('tickets')[i].href + "=" + status + "\\n";
            }
            if (newTicket != "")
            {
              links = links + newTicket + "=True";
            }
            // replace '/' with '~~'
            links = links.replace(/\//g, "~~");

            //doc.getElementsByName('tickets')[0].href
            //doc.getElementsByName('tickets')[0].text
            //doc.getElementById(doc.getElementsByName('tickets')[0].text).value
            if(SN == "") {
              alert("Enter serial");
              return;
            }
            if(rackU == "") {
              alert("Enter rackU");
              return;
            }
            if(project == "") {
              project = "Infrastructure";
            }
            if(owner == "") {
              owner = "Infrastructure";
            }
            debugger;
            var config = encodeURI('sn=' + SN + '\\nBC=' + BC + '\\nserverRoom=' + serverRoom + '\\nrack=' + rack + '\\nrackU=' + rackU + '\\nproject=' + project + '\\nowner=' + owner + '\\nHardware=' + hardware + '\\nnotes=' + notes + '\\npowered=' + powered + '\\ncategory=' + category + '\\ncolor=' + color + '\\n' + links );

            var URL = '/admin/scan/""" + lab + """/' + SN + '.config/' + config + '/down/' + window.pageYOffset;
            window.open(URL,"_self");
        }


        </script>

        """

def loadEnv():
    global HWTypes
    global LabSpace
    global colorMap
    global USER_COLORS
    global users
    global categorys

    with open(scriptPath + "/env.config") as fh:
        for line in fh.readlines():
            line = line.strip()
            if line.startswith('#') or line.strip() == "":
                continue
            #add HWTypes
            #[TYPE] <name>:<U space>#color
            if line.startswith('['):
                name, size = line.split(":")
                HWTypes[name] = [size]
            #add lapspace
            #LabName:Racks/RackSize,Racks/RackSize
            elif "=#" in line:
                name,colorNdescription = line.split('=#')
                colorMap[name] = colorNdescription.split(':')
            elif line.startswith('USER_COLORS:'):
                USER_COLORS = line.split(":")[-1].strip().split(' ')
            elif line.startswith('user:'):
                username = line.split(':')[1]
                password = line.split(':')[2].strip()
                users[username] = password
            elif line.startswith('category'):
                categorys.append(line.split(':')[-1].strip())
            else:
                labName,racksRaw = line.split(':')
                LabSpace[labName] = {}
                for rack in racksRaw.split(","):
                    rack,u = rack.split("/")
                    LabSpace[labName][rack] = u

    #map colors and hardware
    for name in HWTypes:
        hwType = name.split(']')[0].strip('[')
        HWTypes[name].append(colorMap[hwType][0])

loadEnv()

def legendHTML():
    returnHTML = f"""
    <!-- The Legend -->
    <div id="myLegend" class="legend">
      <!-- Legend content -->
      <div class="legend-content">
        <span class="close">&times;</span>
    """
    returnHTML = returnHTML + "<div class='grid-item' style='padding: 15px; background-color: #8fbfbf;'> <span class='blinking'>Blinking: Open Ticket</span></div>"
    returnHTML = returnHTML + f"<div class='grid-item' style='padding: 15px; background-color: #8fbfbf; background: linear-gradient(to bottom left, #8fbfbf 70%, #cc2900);'>Red: Power is off</div>"

    returnHTML = returnHTML + f"<div class='grid-item' style='padding: 15px; background-color: #8fbfbf; background: linear-gradient(to bottom left, #33ff55, #8fbfbf, #8fbfbf,#8fbfbf, #8fbfbf);'>Top Color: Colorized by owner</div>"

    returnHTML = returnHTML + f"<div class='grid-item' style='padding: 15px; background-color:{InfrastructureColor} ;'>Owned by Infrastructure</div>"

    #returnHTML = returnHTML + '<br><br>Hardware by color:<br><div class="grid-container">'
    for typeName in colorMap.keys():
        color = colorMap[typeName][0]
        description = colorMap[typeName][1]
        returnHTML = returnHTML + f'<div class="grid-item" style="background-color: {color};">' + description  + "</div>"
    returnHTML = returnHTML +  "</div>\n</div> \n </div>"
    return returnHTML

def ipmiUserHTML():
    returnHTML = f"""
    <!-- The Legend -->
    <div id="ipmi" class="ipmiPopup">
      <div id="updateIPMI" >
        <a href="javascript:updateIPMI('');">Submit login</a>
      </div>
      <div class="ipmi-content" id="ipmi-content">
        <span class="close">&times;</span>
    """
    returnHTML = returnHTML +  "</div>\n</div> \n </div>"
    return returnHTML


def labLinks(admin=False):
    returnHtml = "<div id='links'>"
    if admin:
        start = "/admin/"
    else:
        start = "/"
    
    for lab in LabSpace.keys():
        returnHtml = returnHtml + f"<a href='{start}{lab}/index.html'>{lab}</a>&nbsp;"
    returnHtml = returnHtml + "<a href='#filterInput'>Search</a>"
    return returnHtml + '&nbsp;  <button id="myBtn">Open Legend</button></div>'


adminBODY = f"""
<body>
  <div id="updateDiv" display: table; >
    <a href="javascript:updateEdit('');">Update</a>
  </div>
  <div id="ipmiDiv" display: table; >
    <a href="javascript:;" id="ipmiBtn">IPMI</button>
  </div>
  <div id="deleteDiv" display: table; >
    <a href="javascript:deleteServer('');">Delete</a>
  </div>
  <div id="colorDiv" display: table; >
    <a href="javascript:showColor();">Custom Color</a>
  </div>
  <input id=pickColor class="jscolor" value="" style="display: none; position: fixed; top: 30px; left: 280px; width: 65px;"> <br>

  {labLinks(admin=True)}
  {legendHTML()}
  {ipmiUserHTML()}
"""

BODY = f"""
<body>
{labLinks()}
{legendHTML()}
"""


def ticketAsHTML(ticket, value="Open"):
    returnHtml = f"<select id='{ticket}'>"
    if value == 'Open':
        returnHtml = returnHtml + f"\n  <option selected='selected' value='{value}'>Open</option>"
        returnHtml = returnHtml + f"\n  <option value='False'>Closed</option>"
    else:
        returnHtml = returnHtml + f"\n  <option selected='selected' value='False'>Closed</option>"
        returnHtml = returnHtml + f"\n  <option value='True'>Open</option>"
    return returnHtml + "\n</select>"

def powerAsHTML(value="True"):
    returnHtml = "<select id='powered'>"
    if value == 'True':
        returnHtml = returnHtml + f"\n  <option selected='selected' value='{value}'>Powered</option>"
        returnHtml = returnHtml + f"\n  <option value='False'>Off</option>"
    else:
        returnHtml = returnHtml + f"\n  <option selected='selected' value='False'>Off</option>"
        returnHtml = returnHtml + f"\n  <option value='True'>Powered</option>"
    return returnHtml + "\n</select>"

def categorysAsHTML(value=""):
    global categorys
    returnHtml = "<select id='categorys'>"
    for category in categorys:
        if value == category:
            returnHtml = returnHtml + f"\n  <option selected='selected' value='{value}'>{value}</option>"
        else:
            returnHtml = returnHtml + f"\n  <option value='{category}'>{category}</option>"
    return returnHtml + "\n</select>"

def hardwareAsHTML(value=""):
    returnHtml = "<select id='Hardware'>"
    for hw in HWTypes.keys():
        if hw == value:
            returnHtml = returnHtml + f"\n  <option selected='selected' value='{hw}'>{hw}</option>"
        else:
            returnHtml = returnHtml + f"\n  <option value='{hw}'>{hw}</option>"
    return returnHtml + "\n</select>"

def racksAsHTML(value="", filterLab=""):
    returnHtml = "<select id='rack'>"
    for lab in LabSpace.keys():
        if filterLab not in lab:
            continue
        for rack in LabSpace[lab].keys():
            if rack == value:
                returnHtml = returnHtml + f"\n  <option selected='selected' value='{rack}'>{rack} ({lab})</option>"
            else:
                returnHtml = returnHtml + f"\n  <option value='{rack}'>{rack} ({lab})</option>"
    return returnHtml + "\n</select>"



def serverRoomsAsHTML(value="", filterLab=""):
    returnHtml = "<select id='serverRoom'>"
    for lab in LabSpace.keys():
        if filterLab not in lab:
            continue
        if lab == value:
            returnHtml = returnHtml + f"\n  <option selected='selected' value='{lab}'>{lab}</option>"
        else:
            returnHtml = returnHtml + f"\n  <option value='{lab}'>{lab}</option>"
    return returnHtml + "\n</select>"







    #debug("YOYO:" + str(allData))
    returnHtml = f"""
    """



def newEditBox(filterLab=''):
    return f"""
    <div id='editServer' display: table;>
        SN: <input type="text" value="" id="SN">
        <br>
        BC: <input type="text" value="" id="BC"><br>
        <hr>
        {hardwareAsHTML()}
        <br>
        {serverRoomsAsHTML(filterLab=filterLab)}
        <br>
        {racksAsHTML(filterLab=filterLab)}
        <br>
        RackU: <input size="2" type="text" value="" id="rackU">
          <br><hr>
        Project: <input type="text" value="" id="project">
          <br>
        Owner: <input type="text" value="" id="owner">
          <br>
        Notes: <input type="text" value="" id="notes">
          <br>
        {powerAsHTML()}
          <br>
        {categorysAsHTML()}
          <hr>
        New Ticket: <input type="text" value="" id="newTicket"><br>

    </div>
    """

def checkTickets(allData):
    for key in allData:
        if 'http' in key:
            if allData[key] == "True":
                return True
    return False

def preLoadEditBox(allData, filterLab=""):
    if 'BC' not in allData.keys():
        allData['BC'] = ""
    #debug("YOYO:" + str(allData))

    #ticket code
    tickets = ""
    category = ""
    for key in allData.keys():
        #debug(key)
        if "category" in key:
            category = allData['category']
        if "http" in key:
            name = key.split("/")[-1]
            if allData[key] == "True":
                tickets = tickets + f'Ticket: <a name="tickets" target="_blank" style="background-color: FF0000;" href="{key}">{name}</a>'
                tickets = tickets + ticketAsHTML(name, value="Open")
            else:
                tickets = tickets + f'Ticket: <a name="tickets" target="_blank" style="background-color: 00FF00;" href="{key}">{name}</a>'
                tickets = tickets + ticketAsHTML(name, value="Closed")
            tickets = tickets + "\n<br>\n"
    tickets = tickets + """
    New Ticket: <input type="text" value="" id="newTicket"><br>
    """

    returnHtml = f"""
    BC: <input type="text" value="{allData['BC']}" id="BC"><br>
    <hr>
    {hardwareAsHTML(allData['Hardware'])}
    <br>
    {serverRoomsAsHTML(value=allData['serverRoom'], filterLab=filterLab)}
    <br>
    {racksAsHTML(value=allData['rack'], filterLab=filterLab)}
    <br>
    RackU: <input size="2" type="text" value="{allData['rackU']}" id="rackU">
    <br><hr>
    Project: <input type="text" value="{allData['project']}" id="project">
    <br>
    Owner: <input type="text" value="{allData['owner']}" id="owner">
    <br>
    Notes: <input type="text" value="{allData['notes']}" id="notes">
    <br>
    {powerAsHTML(allData['powered'])}
    <br>
    {categorysAsHTML(value=category)}
    <br><hr>
    <input id=pickColor class="jscolor" value="" style="display: none;"> <br>
    """

    return f'SN: <input type="text" value="{allData["sn"]}" id="SN"><br>' + returnHtml + tickets



def loadConfigFromString(config):
    returnData = {}
    for line in config.split('\n'):
        if line.strip() == "":
            continue
        try:
            returnData[line.split('=')[0]] = line.split('=')[1].strip()
        except Exception:
            debug("Error reading: " + line)
    return returnData



def getFileName(serverRoom,rack,RackU,sn):
    return f"{scriptPath}/configs/{serverRoom}/{rack}/{sn}.config"

def saveConfig(sn="" ,serverRoom="",rack="", rackU="", project="", owner="", IP='', Type='', note='', powerOn=True):
    fileName = getFileName(serverRoom,rack,rackU,sn)
    filePath = os.path.dirname(fileName)
    if project == "":
        project = "Infrastructure"
    if owner == "":
        owner = "Infrastructure"
    fileData = f"sn={sn}\nserverRoom={serverRoom}\nrack={rack}\nrackU={rackU}\nproject={project}\nowner={owner}\nHardware={Type}\nnotes={note}\npowered={powerOn}"

    #make dir
    os.makedirs(filePath, exist_ok=True)
    #make file
    with open(fileName, 'w') as fh:
        fh.write(fileData)

def storageToHTML(storage):
    if storage == {}:
        return ""
    returnHtml = """
    <table class='storage'>
    <tr>
      <th>Storage items</th>
      <th>Count</th>
      <th>note</th>
    </tr>"""
    for typeName in storage:
        data = storage[typeName]
        note = ""
        if isinstance(data[0], list):
            size = len(data)
            note = data[0][-1]
            for item in data:
                if item[-1] != "":
                    note = item[-1]
                    break
            #debug(f"{note} {data}")
        else:
            size = data[0]
            note = data[1]

        returnHtml = returnHtml + f"<tr><th class='storage'>{typeName.split('.')[0]}</th><th class='storage'>{size}</th><th>{note}</th></tr>"
    return returnHtml + "\n</table>"

def loadStorage(lab):
    pathName = f'{scriptPath}/configs/{lab}/storage/'
    if not os.path.exists(pathName):
        return {}
    typeNames = os.listdir(pathName)
    types = {}
    for ty in typeNames:
        with open(pathName + ty) as fh:
            lines = fh.readlines()
            SNs = []
            for line in lines:
                if line.strip('') == "":
                    continue
                if line.startswith('quantity'):
                    allData = readConfigFile(pathName + ty)
                    types[ty] = [allData['quantity'],allData['note']]
                    break
                else:
                    note = ""
                    if ":" in line:
                        line, note = line.split(":")
                    SNs.append([line.strip(),note])
            if SNs != []:
                types[ty] = SNs
    return types


def loadLabData():
    
    #find labs
    labNames = os.listdir(scriptPath + "/configs/")
    labs = {}
    ipmiConfigs = {}
    for labName in labNames:
        labs[labName] = {}
        racks =  os.listdir(scriptPath + "/configs/" + labName + "/")
        for rack in racks:
            labs[labName][rack] = {}
            servers = os.listdir(scriptPath + "/configs/" + labName + "/" + rack + "/")
            for server in servers:
                if server.endswith('.config'):
                    labs[labName][rack][server] = readConfigFile(scriptPath + "/configs/" + labName + "/" + rack + "/" + server)
                elif server.endswith('.ipmi'):
                    ipmiConfigs[server.split('.')[0]] = scriptPath + "/configs/" + labName + "/" + rack + "/" + server
    return([labs, ipmiConfigs])

#used to find storage types/lab
def getKnownTypes(lab):
    filePath =  f"{scriptPath}/configs/{lab}/storage/"
    returnData = []
    if os.path.exists(filePath):
        for item in os.listdir(filePath):
            if ".config" in item:
                name = item.split('.')[0]
                if name != "":
                    returnData = returnData + [name]
    return returnData


#write list of SN OR a quantity to a file
def writeStorage(lab, itemType, quantity=0, SN="", note=""):
    filePath = f"{scriptPath}/configs/{lab}/storage/"
    fileName = filePath + f"{itemType}.config"
    os.makedirs(filePath, exist_ok=True)
    if SN != "":
        #TODO check for quantity in file first
        with open(fileName, "a") as fh:
            fh.write("\n" + SN + ":" + note)
    elif quantity != 0:
        with open(fileName, "w+") as fh:
            fh.write(f"quantity={quantity}\nnote={note}")


def createLable(project, owner):
    if project.strip() == owner.strip():
        return project
    return f"{project[:14]}: {owner[:14]}"

def rack2Table(rack):
    #<tr> <td>{lab}</td> <td>{rack}</td> <td>{rackU}</td> <td>{project}</td> <td>{owner}</td> <td>{notes}</td> <td>{power}</td> <td>{Hardware}</td> <td>{sn}</td>
    returnData = ""
    for server in rack:
        lab = rack[server]['serverRoom']
        rackName = rack[server]['rack']
        rackU = rack[server]['rackU']
        project = rack[server]['project']
        owner = rack[server]['owner']
        notes = rack[server]['notes']
        power = rack[server]['powered']
        Hardware = rack[server]['Hardware']
        sn = rack[server]['sn']
        if 'category' in rack[server]:
            category = rack[server]['category']
        else:
            category = ""
            
        if 'BC' in rack[server]:
            BC = rack[server]['BC']
        else:
            BC = ""
            
        returnData = returnData + f"<tr> <td>{lab}</td> <td>{rackName}</td> <td>{rackU}</td> <td>{project}</td> <td>{owner}</td> <td>{notes}</td> <td>{power}</td> <td>{Hardware}</td> <td>{category}</td> <td>{sn}</td> <td>{BC}</td>\n"
    return returnData


def hoverHTML(allData, IPMI_data=""):
    if IPMI_data != "":
        errors = IPMI_data.split('|')[2]
        heat = IPMI_data.split('|')[0:2]
    else:
        errors = ""
        heat = [0,0]
    lab = allData['serverRoom']
    rackName = allData['rack']
    rackU = allData['rackU']
    project = allData['project']
    owner = allData['owner']
    notes = allData['notes']
    power = allData['powered']
    #find open tickets
    openTickets = ""
    for key in allData:
        if 'http' in key:
            if allData[key] == 'True':
                openTickets = openTickets + f"<a style='color: red;' target='_blank' href='{key}'>{key.split('/')[-1]}</a>&nbsp;"
    if power == "True":
        power = "On"
    elif power == "False":
        power = "Off"
    Hardware = allData['Hardware']
    sn = allData['sn']
    returnHTML = f'''
    Project:&nbsp; {project}<br>
    Owner:&nbsp; {owner}<br>
    Hardware:&nbsp; {Hardware}<br>
    Power:&nbsp; {power}<br>
    Notes:&nbsp; {notes}<br>
    Tickets:&nbsp; {openTickets}
    '''
    if errors != 'OK' and errors != "":
        returnHTML = "IPMI errors:<br>&nbsp;&nbsp;" + errors + "<br><br>" + returnHTML
    elif errors == 'OK':
        returnHTML = "IPMI working:<br>" + f"Front temperature: {heat[0]}<br>\nBack temperature: {heat[1]}<br>" + returnHTML
    return returnHTML

#If BLANK is true rack is used for rackname
def rack2Html(rack, size=42, BLANK=False, tooltip=False, filterLab=""):
    global USER_COLORS
    global colorIndex
    global USED_COLORS
    
    if filterLab == "":
        filterLab = "all"
        
    if BLANK:
        rackName = rack
        rack = []
    else:
        try: #this can error out if we have an empty lab folder
            rackName = rack[list(rack.keys())[0]]['rack']
        except Exception:
            #Use Blank rack
            BLANK=True
            rackName = "No Data" #Cannot recover name :S
            rack = []

    rackData = [None] * (size +1) #rackData[someU] = rackU, aka [0] is unused
    returnHtml = '<table class="rack" border="0" cellspacing="0" cellpadding="1">\n<tbody><tr><th width="10%">&nbsp;</th> <th width="80%">' + str(rackName) + '</th> <th width="10%">&nbsp;</th> </tr>'
    for server in rack:
        #debug(rack.keys())
        #debug(rack[server])
        #debug(server)
        try:
            rackU = int(rack[server]['rackU'])
        except Exception:
            debug('Error reading server data...' + str(rack[server]))
            continue
        server = rack[server]
        if rackU <= len(rackData):
            if rackData[rackU] == None:
                rackData[rackU] = server
            else:
                lab = server['serverRoom']
                rack_name = server['rack']
                lable = server['sn']
                bad_file1 = f"{scriptPath}/configs/{lab}/{rack_name}/{lable}.config"
                
                lab = rackData[rackU]['serverRoom']
                rack_name = rackData[rackU]['rack']
                lable = rackData[rackU]['sn']
                bad_file2 = f"{scriptPath}/configs/{lab}/{rack_name}/{lable}.config"
                
                debug(f'\n\n----------------------\nDuplicate entry in: {lab} {rack_name} {rackU} removing:\n{bad_file1}\nand keeping\n{bad_file2}\n------------------------')
                #TODO remove the oldest file, This is more or less random.
                os.remove(bad_file1)
        else:
            #error, Server not in U of rack
            debug("Error, Server out of U: " +str(rackData))
            server['project'] = "U Error: " + server['project']
            rackData[-1] = server
        
    i = size
    while i > 0:
        if rackData[i] == None:
            returnHtml = returnHtml + f'<tr><th>{i}</th><td class="atom state_F"><div title="Free rackspace">&nbsp;</div><th>{i}</th></td></tr>' + "\n"
            i = i - 1
        else:
            #debug(rackData[i].keys())
            uSize = int(HWTypes[rackData[i]['Hardware']][0])
            #setup color (powered off = red + strike)
            project = rackData[i]['project']
            lable = rackData[i]['sn']
            lab = rackData[i]['serverRoom']
            owner = rackData[i]['owner']
            rack = rackData[i]['rack']
            powered = rackData[i]['powered']
            color = ""
            heat = [0,0]
            errors = ""
            log_file = f"{scriptPath}/configs/{lab}/{rack}/{lable}.log"
            lastLog = ""
            if os.path.isfile(log_file):
                #TODO check log in not too old
                lastLog = list(tail(log_file, n=1))[0].decode('UTF-8')
                debug("WORKING: " + lastLog)
                heat = lastLog.split('|')[0:2]
                errors = lastLog.split('|')[2]
                powered = lastLog.split('|')[3]
                rackData[i]['powered'] = powered
            #setup owner color
            #set ownerBuffer to 6 chars
            ownerBuffer = owner
            if len(ownerBuffer) < 6:
                ownerBuffer = ownerBuffer + '~' * (6 - len(ownerBuffer))
            else:
                ownerBuffer = ownerBuffer[:6]

            ownerKey = project + owner
            if ownerKey not in USED_COLORS:
                USED_COLORS[ownerKey] = USER_COLORS[colorIndex]
                colorIndex = colorIndex + 1
                if colorIndex >= len(USER_COLORS):
                    colorIndex = 0
            ownerColor = USED_COLORS[ownerKey]



            configPath = f"configs/{filterLab}/{lab}/{rackName}/{lable}.config"
            name = createLable(project, owner)
            #make Infrastructure purple
            if owner == "Infrastructure":
                color = InfrastructureColor.strip('#')
                ownerColor = InfrastructureColor.strip('#')

            #overwrite color if needed
            if 'color' in rackData[i].keys():
                color = rackData[i]['color']
            elif color == "":
                color = HWTypes[rackData[i]['Hardware']][1]

            #powered off server have a red gradient
            if powered == "False":
                if owner == "Infrastructure":
                    color1 = InfrastructureColor.strip('#')
                else:
                    if 'color' in rackData[i].keys():
                        color1 = rackData[i]['color']
                    else:
                        color1 = HWTypes[rackData[i]['Hardware']][1]

                color = f"#{color1}; background: linear-gradient(to bottom left, #{ownerColor}, #{color1}, #{color1},#{color1}, {powerOffColor})"
                name = f"<strike style='color: #600e00'>" + name + "</strike>"
            else:
                color = f"#{color}; background: linear-gradient(to bottom left, #{ownerColor}, #{color}, #{color},#{color}, #{color})"


            if checkTickets(rackData[i]):
                name = "<span class='blinking'>" + name + "</span>"
            if errors != "OK" and errors != "":
                name = "<span class='blinking'>" + name + "|IPMI Errors" + "</span>"
            #<div class="tooltip">Hover over me
            #<span class="tooltiptext">Tooltip text</span>
            #</div>
            if tooltip:
                tooltipHtml = hoverHTML(rackData[i], lastLog)
                returnHtml = returnHtml + f'<tr><th>{i}</th><td class="atom state_T" colspan="1" style="background-color: {color};" rowspan="{uSize}"><div name="{lable}"><div class="tooltip">{name}<span class="tooltiptext">{tooltipHtml}</span></div></div><th>{i}</th></td></tr>' + "\n"
            else:
                returnHtml = returnHtml + f'<tr><th>{i}</th><td class="atom state_T" colspan="1" style="background-color: {color};" rowspan="{uSize}"><div title="{lable}"><a href="javascript:load_server(\'/{configPath}\');">{name}</a></div><th>{i}</th></td></tr>' + "\n"
            if uSize > 1:
                for q in reversed(range(i - uSize+2, i +1)):
                    returnHtml = returnHtml + f"<tr><th>{q-1}</th><th>{q-1}</th></tr>"
            i = i - uSize
    #debug(i)
    return returnHtml + "</tbody></table>"

#TODO display unused racks as well
#load edit data for loadU Unless set to -1
def createHtml(loadU=-1, loadLab="", loadRack="", lastRack={}, scroll=0, admin=True, snNA=False, filterLab=""):

    if admin:
        bodyHtml = adminBODY
    else:
        bodyHtml = BODY
    #newEditBox preLoadEditBox
    if loadU < 0:
        returnHtml = CSS + JS(scroll=scroll, admin=admin,lab=filterLab) + bodyHtml
        #only show nexEditBox if admin.
        if admin:
            returnHtml = returnHtml + newEditBox(filterLab=filterLab)
    else:
        #TODO find allData for
        allData = []


        serversAtCount = serverAtU(loadLab,loadRack,loadU)
        
        if len(serversAtCount) < 1:
            allData = []
        else:
            allData = readConfigFile(serversAtCount[0])

        if allData == [] and lastRack != {}:
            #update rackU
            lastRack['rackU'] = loadU
            #remove old SN
            lastRack['sn'] = ""
            #remove old tickets
            for key in list(lastRack.keys()):
                if 'http' in key:
                    del(lastRack[key])
            allData = lastRack
        if allData != []:
            #load box with last server data
            #debug("Info: " + preLoadEditBox(allData))
            if snNA:
                allData['sn'] = 'na'
            #reset barcode
            allData['BC'] = ''
            returnHtml = CSS + JS(scroll=scroll,lab=filterLab) + bodyHtml + "<div id='editServer' display: table;>" + preLoadEditBox(allData) + "</div>"
        else:
            #we did not fine a server at U
            returnHtml = CSS + JS(scroll=scroll,lab=filterLab) + bodyHtml + newEditBox(filterLab=filterLab) #I don't think this is called anymore TODO

    if admin:
        filteredTableHtml = "<div style='float:right; width: 80%; padding-top: 15px;'>"
    else:
        filteredTableHtml = "<div style='float:right; width: 100%; padding-top: 15px;'>"
    filteredTableHtml = filteredTableHtml + """
    <input type="text" id="filterInput" onkeyup="filterFunction()" placeholder="Filter" title="Type in a name">
    <table id="filterTable">
    <tr class="header">
      <th style="width:10%;">Lab</th>
      <th style="width:3%;">Rack</th>
      <th style="width:2%;">RackU</th>
      <th style="width:10%;">Project</th>
      <th style="width:10%;">Owner</th>
      <th style="width:15%;">Notes</th>
      <th style="width:5%;">Power</th>
      <th style="width:15%;">Hardware</th>
      <th style="width:10%;">Category</th>
      <th style="width:5%;">SN</th>
      <th style="width:5%;">BC</th>
    </tr>"""


    labs = loadLabData()[0] #labs that have data for
    allLabs = list(LabSpace.keys())


    #rack html
    if admin:
        returnHtml = returnHtml + "<div id='Racks' style='float:right; width: 80%;'>"
    else:
        returnHtml = returnHtml + "<div id='Racks' style='float:center; width: 90%;'>"
    for lab in allLabs:
        #only show needed lab
        if filterLab != "" and filterLab not in lab:
            continue
        returnHtml = returnHtml + f"\n<div id='{lab.replace(' ', '')}' style='float:right; width: 100%;'><h1>" + lab + "</h1><br>"
        storage = loadStorage(lab)
        if lab in labs:
            racks = labs[lab] #Racks we have data for
        else:
            racks = []
        allRacks = list(LabSpace[lab].keys())
        for rack in allRacks:
            #todo LabSpace['Lights Out'] = {'Rack2':1,'rack3':4,'rack4':5,'rack5':6,'rack6':7,'rack7':8,'rack8':9,'rack9':10,'rack10':11,'rack11':12,'rack12':13,'rack13':14}
            if rack in racks:
                returnHtml = returnHtml + rack2Html(labs[lab][rack], size=int(LabSpace[lab][rack]), tooltip=not admin, filterLab=filterLab)
                filteredTableHtml = filteredTableHtml + rack2Table(labs[lab][rack])
            else:
                returnHtml = returnHtml + rack2Html(rack,BLANK=True, size=int(LabSpace[lab][rack]), tooltip=not admin, filterLab=filterLab)
        returnHtml = returnHtml + storageToHTML(storage)
        returnHtml = returnHtml + "\n</div>"
    returnHtml = returnHtml + "</div>" + filteredTableHtml + "</table>"
    return returnHtml + "</body>"


def readConfigFile(fileName):
    returnData = {}
    try:
        with open(fileName) as fh:
            for line in fh.readlines():
                if line.strip() == "" or line.startswith('#'):
                    continue
                if not line.strip().endswith('='):
                    returnData[line.split('=')[0]] = line.split('=')[1].strip()
                else:
                    returnData[line.strip()[:-1]] = ""
    except Exception as e:
        debug(f"Error reading '{fileName}' {e}")
        raise(e)
    return returnData



def debug(error):
    with open('/tmp/debug.txt', 'a+') as debugLog:
        debugLog.write(str(error) + "\n")





def serverAtU(lab,rack,rackU):
    rackU = str(rackU)
    foundServers = []
    rackDir = f"{scriptPath}/configs/{lab}/{rack}/"
    #debug("RackDir: " + rackDir)
    try:
        serversInRack = os.listdir(rackDir)
    except Exception:
        debug("FAIL3")
        return foundServers
    for server in serversInRack:
        #debug(server)
        with open(rackDir + server) as fh:
            for line in fh.readlines():
                #debug(f"Reading {line}")
                if line.startswith("rackU="):
                    if line.split('=')[-1].strip() == rackU:
                        #debug(f"Found {line}")
                        foundServers.append(rackDir + server)

    #debug(foundServers)
    return foundServers

def serverWithSN(searchSN):

    foundServers = []
    labs = loadLabData()[0] #labs that have data for
    for lab in labs:
        racks = labs[lab]
        for rack in racks:
            rackDir = f"{scriptPath}/configs/{lab}/{rack}/"
            try:
                serversInRack = os.listdir(rackDir)
            except Exception:
                continue
            for server in serversInRack:
                with open(rackDir + server) as fh:
                    for line in fh.readlines():
                        #debug(f"Reading {line}")
                        if line.startswith("sn="):
                            if line.split('=')[-1].strip() == searchSN:
                                foundServers.append(rackDir + server)

    return foundServers

def main(stdscr):
    #setup COLOR
    curses.use_default_colors()
    for i in range(0, 8):
            #curses.init_pair(i, 0, i);
        if i == 7:
            curses.init_pair(i, -1, -1)
        else:
            curses.init_pair(i, i, -1) #with default backgound
    curses.init_pair(8,7,1)
    global rack
    global rackU
    global spacing
    global owner
    global project
    global hardware
    global lab
    global note
    global powerState
    global itemType

    note = ""
    htmlOrScan = menu(stdscr, "New Scan", "Update Html", title="InventoryCLI")
    if htmlOrScan == "Update Html":
        html = createHtml()
        with open("./index.html", "w") as fh:
            fh.write(html)
        menu(stdscr, "Okay", title="Updated ./index.html")
        exit()

    lab = menu(stdscr, list(LabSpace.keys()), title="Which Lab?")

    #hardware = menu(stdscr, list(HWTypes.keys()), "Select hardware")
    rack = menu(stdscr, list(LabSpace[lab].keys())+ ['Storage'], title="Which Rack?")
    if rack != "Storage":
        #add servers in rack
        rackU = prompt(stdscr, "" , title="Enter Rack U?")
        direction = menu(stdscr, "Top Down","Bottom Up" , title="Enter scanning direction")
        powerState = True

        if direction == "Bottom Up":
            spacing = spacing * -1

        while True:
            scanMenu(stdscr)
    else:
        #add stuff in Storage
        itemType = ""
        note = ""
        while True:
            storageMenu(stdscr)
    exit()


def getIP():
    import socket
    #Thanks: https://stackoverflow.com/a/1267524/5282272
    return (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]

#Thanks https://stackoverflow.com/a/136280
def tail(f, n=12):
    proc = subprocess.Popen(['tail', '-n', str(n), f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines


def read_ipmi_file(path):
    returnData = {}
    with open(path) as fh:
        for line in fh.readlines():
            if line != "" and not line.startswith("#"):
                rawData = line.split(':')
                returnData['ip'] = rawData[0]
                returnData['user'] = rawData[1]
                returnData['password'] = rawData[2].strip()
    return returnData

def IPMI_write_log(config, raw_temp, errorsNpower):
    logName = config[:-5] + ".log"
    stuff_2_write = ""
    front = 0
    back = 0
    for line in raw_temp.split("\n"):
        #INTEL
        if "Front Panel Temp" in line:
            front = line.split('|')[-1].split('d')[0].strip()
        if "Exit" in line:
            back = line.split('|')[-1].split('d')[0].strip()
        #SMC (No Front)
        if "System Temp" in line:
            back = line.split('degrees')[0].split("|")[-1].strip()
    #setup error string
    errors = ", ".join(errorsNpower[0])
    power = errorsNpower[1]
    #if no errors
    if errors == "":
        errors = "OK"
    tempString = f"{front}|{back}|{errors}|{power}|{datetime.now()}"
    if tempString != "":
        with open(logName, 'a+') as fh:
            fh.write(tempString + "\n")
            
def IPMI_cmd_str(server):
    return f"ipmitool -I lanplus -H {server['ip']} -U {server['user']} -P {server['password']} "


def IPMI_health_check(server):
    cmd = IPMI_cmd_str(server) + "chassis status"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    errors_found = []
    power = False
    if p.returncode == 0:
        out = out.decode('UTF-8')
        for line in out.split('\n'):
            for test in IPMI_should_be_false:
                if test in line:
                    if 'false' not in line:
                        errors_found.append(test)
                if 'System Power' in line:
                    if 'on' in line:
                        power = True
        return [errors_found, power]
    else:
        return [err.decode('UTF-8')]

def IPMI_ping(server, config):
    global IPMI_WORKING
    global IPMI_BROKEN
    #ipmitool -I lanplus -H ip -U user -P pass sdr elist full
    cmd = IPMI_cmd_str(server) + "sdr elist full"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    
    if p.returncode != 0:
        print("IPMI connection error! File:\n  " + config + "\n  " + str(err) + "\n  " + cmd)
        
        if config in IPMI_WORKING:
            del(IPMI_WORKING[config])
        IPMI_BROKEN[config] = err.decode('UTF-8')
    else:
        #do something out output
        if config in IPMI_BROKEN:
            del(IPMI_BROKEN[config])
        IPMI_WORKING[config] = out.decode('UTF-8')
        IPMI_write_log(config, out.decode('UTF-8'), IPMI_health_check(server))
        
        
IPMI_Threads = []
def IPMI_listener():
    ipmiConfigs = loadLabData()[1]
    lastKnown = {}
    waitForIt = ipmiWaitTime
    while True:
        #update asap if we found a new config
        if lastKnown != ipmiConfigs:
            lastKnown = ipmiConfigs
            waitForIt = 0
        #run ipmi update
        if waitForIt <= 0:
            ipmiConfigs = loadLabData()[1]
            waitForIt = ipmiWaitTime
            for fileName in ipmiConfigs:
                server = read_ipmi_file(ipmiConfigs[fileName])
                IPMI_Threads.append(threading.Thread(target=IPMI_ping, args=(server,ipmiConfigs[fileName],)))
                IPMI_Threads[-1].daemon = True
                IPMI_Threads[-1].start()
                #IPMI_ping(server, fileName)
        waitForIt = waitForIt -1
        time.sleep(1)

#starup IPMIlistener
t = threading.Thread(target=IPMI_listener)
t.daemon = True
t.start()

#run with gevent in production
#needs root
if __name__ == '__main__':
    import gevent.pywsgi

    #app_server = gevent.pywsgi.WSGIServer((getIP(), 80), app)
    app_server = gevent.pywsgi.WSGIServer((getIP(), 443), app, keyfile='key.pem', certfile='cert.pem')

    app_server.serve_forever()
