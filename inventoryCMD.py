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


import curses
import curses.textpad
import socket
import sys
import subprocess
import os
import shutil
import time

scriptPath = os.path.dirname(os.path.realpath(__file__))
configFiles = scriptPath + "/configs/"
htmlFile = scriptPath + "/index.html"

LabSpace = {}

HWTypes = {}
#HWTypes[''] = 2



powerOffColor = "#cc2900"

colorCodes = {'43':2,'44':2,'02':3,'2f':2, '12':0}
hardware = ""
project = ""
owner = ""
#7 = black
#6 = light blue
#5 = purple
#4 = blue
#3 = tan
#2 = green
#1 = red


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

#myInput {
  background-position: 10px 10px;
  background-repeat: no-repeat;
  width: 100%;
  font-size: 16px;
  padding: 12px 20px 12px 40px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}

#myTable {
  border-collapse: collapse;
  width: 100%;
  border: 1px solid #ddd;
  font-size: 18px;
}

#myTable th, #myTable td {
  text-align: left;
  padding: 12px;
}

#myTable tr {
  border-bottom: 1px solid #ddd;
}

#myTable tr.header, #myTable tr:hover {
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

</style>
"""
  
JS = """
<script>
function myFunction() {
  var input, filter, table, tr, td, i, txtValue, allText, sections;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");
  for (i = 0; i < tr.length; i++) {
    allText = "";
    sections = tr[i].getElementsByTagName("td");
    for (e = 0; e < sections.length; e++) {
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
</script>

"""

def loadConfig():
  global HWTypes
  global LabSpace
  
  with open(scriptPath + "/env.config") as fh:
    for line in fh.readlines():
      line = line.strip()
      if line.startswith('#') or line == "":
        continue
      #add HWTypes
      #[TYPE] <name>:<U space>#color
      if line.startswith('['):
        name, sizeColor = line.split(":")
        HWTypes[name] = sizeColor.split("#")
      #add lapspace
      #LabName:Racks/RackSize,Racks/RackSize
      else:
        labName,racksRaw = line.split(':')
        LabSpace[labName] = {}
        for rack in racksRaw.split(","):
          rack,u = rack.split("/")
          LabSpace[labName][rack] = u


def getFileName(serverRoom,rack,RackU,sn):
  return f"{scriptPath}/configs/{serverRoom}/{rack}/{sn}.config"

def saveConfig(sn="" ,serverRoom="",rack="", rackU="", project="", owner="", IP='', Type='', note='', powerOn=True):
  fileName = getFileName(serverRoom,rack,rackU,sn)
  filePath = os.path.dirname(fileName)
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
      debug(f"{note} {data}")
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
  for labName in labNames:
    labs[labName] = {}
    racks =  os.listdir(scriptPath + "/configs/" + labName + "/")
    for rack in racks:
      labs[labName][rack] = {}
      servers = os.listdir(scriptPath + "/configs/" + labName + "/" + rack + "/")
      for server in servers:
        labs[labName][rack][server] = readConfigFile(scriptPath + "/configs/" + labName + "/" + rack + "/" + server)
  return(labs)

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
    returnData = returnData + f"<tr> <td>{lab}</td> <td>{rackName}</td> <td>{rackU}</td> <td>{project}</td> <td>{owner}</td> <td>{notes}</td> <td>{power}</td> <td>{Hardware}</td> <td>{sn}</td>\n"
  return returnData

#If BLANK is true rack is used for rackname
def rack2Html(rack, size=42, BLANK=False):
  if BLANK:
    rackName = rack
    rack = []
  else:
    rackName = rack[list(rack.keys())[0]]['rack']

  rackData = [None] * (size +1) #rackData[someU] = rackU, aka [0] is unused
  returnHtml = '<table class="rack" border="0" cellspacing="0" cellpadding="1">\n<tbody><tr><th width="10%">&nbsp;</th> <th width="80%">' + rackName + '</th> <th width="10%">&nbsp;</th> </tr>'
  for server in rack:
    #debug(rack.keys())
    #debug(server)
    rackU = int(rack[server]['rackU'])
    server = rack[server]
    rackData[rackU] = server
    
  i = size
  while i > 0:
    if rackData[i] == None:
      returnHtml = returnHtml + f'<tr><th>{i}</th><td class="atom state_F"><div title="Free rackspace">&nbsp;</div><th>{i}</th></td></tr>' + "\n"
      i = i - 1
    else:
      #debug(rackData[i].keys())
      uSize = int(HWTypes[rackData[i]['Hardware']][0])
      #setup color (powered off = red) 
      if rackData[i]['powered'] == "False":
        color = powerOffColor
      else:
        if 'color' in rackData[i].keys():
          color = rackData[i]['color']
        else:
          color = HWTypes[rackData[i]['Hardware']][1]
      
      project = rackData[i]['project']
      lable = rackData[i]['sn']
      lab = rackData[i]['serverRoom']
      configPath = f"configs/{lab}/{rackName}/{lable}.config"
      returnHtml = returnHtml + f'<tr><th>{i}</th><td class="atom state_T" colspan="1" style="background-color: {color};" rowspan="{uSize}"><div title="{lable}"><a href="{configPath}">{project}</a></div><th>{i}</th></td></tr>' + "\n"
      if uSize > 1:
        for q in range(i,i + uSize - 1):
          returnHtml = returnHtml + f"<tr><th>{q-1}</th><th>{q-1}</th></tr>"
      i = i - uSize
  debug(i)
  return returnHtml + "</tbody></table>"

#TODO display unused racks as well
def createHtml():
  labs = loadLabData() #labs that have data for
  allLabs = list(LabSpace.keys())
  returnHtml = CSS + JS
  filteredTableHtml = """
  <div style='float:left; width: 100%; padding-top: 15px;'>
  <input type="text" id="myInput" onkeyup="myFunction()" placeholder="Filter" title="Type in a name">
  <table id="myTable">
  <tr class="header">
    <th style="width:10%;">Lab</th>
    <th style="width:5%;">Rack</th>
    <th style="width:5%;">RackU</th>
    <th style="width:10%;">Project</th>
    <th style="width:10%;">Owner</th>
    <th style="width:15%;">Notes</th>
    <th style="width:5%;">Power</th>
    <th style="width:15%;">Hardware</th>
    <th style="width:25%;">SN</th>
  </tr>"""
  for lab in allLabs:
    returnHtml = returnHtml + "\n<div style='float:left; width: 100%;'><h1>" + lab + "</h1><br>"
    storage = loadStorage(lab)
    debug(f"Storage: {storage}")
    if lab in labs:
      racks = labs[lab] #Racks we have data for
    else:
      racks = []
    allRacks = list(LabSpace[lab].keys())
    for rack in allRacks:
      #todo LabSpace['Lights Out'] = {'Rack2':1,'rack3':4,'rack4':5,'rack5':6,'rack6':7,'rack7':8,'rack8':9,'rack9':10,'rack10':11,'rack11':12,'rack12':13,'rack13':14}
      if rack in racks:
        debug( f"U{LabSpace[lab][rack]}")
        returnHtml = returnHtml + rack2Html(labs[lab][rack], size=int(LabSpace[lab][rack]))
        filteredTableHtml = filteredTableHtml + rack2Table(labs[lab][rack])
      else:
        returnHtml = returnHtml + rack2Html(rack,BLANK=True, size=int(LabSpace[lab][rack]))
    returnHtml = returnHtml + storageToHTML(storage)
    returnHtml = returnHtml + "\n</div>"
  returnHtml = returnHtml + filteredTableHtml + "</table></div>"
  return returnHtml


def readConfigFile(fileName):
  returnData = {}
  try:
    with open(fileName) as fh:
      for line in fh.readlines():
        returnData[line.split('=')[0]] = line.split('=')[1].strip()
        #print(line)
  except Exception:
    debug(f"Error reading {fileName}.")
  return returnData



def debug(error):
  debugLog = open('./debug.txt', 'a+')
  debugLog.write(str(error) + "\n")
  
      
def prompt(stdscr, txt, title=""):
  screenSize = stdscr.getmaxyx()  
  stdscr.clear()
  if title != "":
    stdscr.move(int(screenSize[0]/2) - 2,0)
    stdscr.addstr(title + "\n",curses.color_pair(7))
  
  #color line
  space = ""
  for na in range(0, screenSize[1]):
    space = space + ' ' 
  stdscr.move(int(screenSize[0]/2) - 1,0)
  stdscr.addstr(space,curses.color_pair(8))
  

  win = curses.newwin(1, int(screenSize[1]/2), int(screenSize[0]/2) -1, len(title) + 1)
  win.bkgd(curses.color_pair(8))
  win.addstr(txt)
  tb = curses.textpad.Textbox(win, insert_mode=False)

  stdscr.refresh()
  text = tb.edit()
  return text.strip()
  #win.addstr(0, 0, text.encode('utf-8'))


def getCurrentServer():
  global rack
  global rackU
  global lab
  
  foundServers = []
  rackDir = f"{scriptPath}/configs/{lab}/{rack}/"
  try:
    serversInRack = os.listdir(rackDir)
  except Exception:
    return foundServers
  for server in serversInRack:
    with open(rackDir + server) as fh:
      for line in fh.readlines():
        #debug(f"Reading {line}")
        if line.startswith("rackU="):
          if line.split('=')[-1].strip() == rackU:
            debug(f"Found {line}")
            foundServers.append(rackDir + server)
  
  #debug(foundServers)
  return foundServers


def storageMenu(stdscr):
  global lab
  global itemType
  global note
  
  #todo get known types and ask if you want to add new
  if itemType == "":
    itemType = menu(stdscr, ["Add New"] + getKnownTypes(lab), title="Enter/Pick item name")
  if itemType == "Add New":
    itemType = prompt(stdscr, "" , title="Enter new item name:")
  
  stdscr.clear()
  stdscr.refresh()
  screenSize = stdscr.getmaxyx()
  
  selectedIndex = 1
  c = ''
  serial = ""
  
  while True:
    #key left right = change u by 1u
    if c == "KEY_LEFT":
      pass
    if c == "KEY_RIGHT":
      pass
    if c == "KEY_UP" and selectedIndex < 3:
      selectedIndex = selectedIndex + 1
      debug(str(selectedIndex))
    elif c == "KEY_DOWN" and selectedIndex > 0:
      selectedIndex = selectedIndex - 1
    elif c == "KEY_BACKSPACE":
      if len(serial) > 0:
        serial = serial[:-1]
        stdscr.clear()
        stdscr.refresh()
      c = ""
      continue
    elif c == "\n":
      if serial != "" and selectedIndex == 0:
        stdscr.clear()
        stdscr.refresh()
        #TODO
        writeStorage(lab, itemType, SN=serial, note=note)
        serial = ""
      #add by quantity
      if selectedIndex == 1:
        selectedIndex = 0
        #TODO read old value
        quantity = prompt(stdscr, "" , title=f"Enter number of {itemType}:")
        note = prompt(stdscr, note, title="Edit Note?")
        #TODO write quantity to file
        writeStorage(lab, itemType, quantity=quantity, note=note)
        itemType = ""
        serial = ""
        return
      elif selectedIndex == 2:
        selectedIndex = 0
        note = prompt(stdscr, note , title="Edit Note?")
      #exit option
      elif selectedIndex == 3:
        html = createHtml()
        with open("./index.html", "w") as fh:
          fh.write(html)
        menu(stdscr, "Okay", title="Updated ./index.html")
        sys.exit()
      c = ''
      continue
      
    else:
      if len(c) != 1:
        debug("Error reading key")
        c = ""
      serial = serial + c
    
    #draw edit hardware
    if selectedIndex == 1:
      stdscr.move(int(screenSize[0]/2) -1,0)
      stdscr.addstr(f"[x] Enter by quantity:",curses.color_pair(7))
    else:
      stdscr.move(int(screenSize[0]/2) -1,0)
      stdscr.addstr(f"[ ] Enter by quantity:",curses.color_pair(7))
    
    #draw edit note part
    if selectedIndex == 2:
      stdscr.move(int(screenSize[0]/2) -2,0)
      if note == "":
        stdscr.addstr("[x] Enter note",curses.color_pair(7))
      else:
        stdscr.addstr(f"[x] Edit: {note}",curses.color_pair(7))
    else:
      stdscr.move(int(screenSize[0]/2) -2,0)
      if note == "":
        stdscr.addstr("[ ] Enter note" + "\n",curses.color_pair(7))
      else:
        stdscr.addstr(f"[ ] Note: {note}",curses.color_pair(7))
    
    #draw exit part
    if selectedIndex == 3:
      txt = "[x] Exit"
      stdscr.move(int(screenSize[0]/2) - 3,0)
      stdscr.addstr(txt + "\n",curses.color_pair(1))
      stdscr.move(int(screenSize[0]/2) + 1,0)
      #stdscr.addstr(serial, curses.color_pair(1))
    else:
      txt = "[ ] Exit" 
      stdscr.move(int(screenSize[0]/2) - 3,0)
      stdscr.addstr(txt + "\n",curses.color_pair(7))

    txt = f"Adding {itemType} with serial: " 
    if selectedIndex == 0:
      stdscr.move(int(screenSize[0]/2),0)
      stdscr.addstr("[x] " + txt,curses.color_pair(1))
      stdscr.move(int(screenSize[0]/2) + 1,0)
      stdscr.addstr(serial, curses.color_pair(1))
    else:
      stdscr.move(int(screenSize[0]/2),0)
      stdscr.addstr("[ ] " +txt,curses.color_pair(7))
      
    c = stdscr.getkey()
    debug("Entered" + str(c))


def scanMenu(stdscr):
  global rack
  global rackU
  global spacing
  global owner
  global project
  global hardware
  global lab
  global note
  global powerState
  
  stdscr.clear()
  screenSize = stdscr.getmaxyx()  
  
  foundOld = False
  serial = ""
  oldFile = ""
  
  serversAtU = getCurrentServer()
  #debug("NEEDED: " + str(serversAtU))
  
  if len(serversAtU) > 1:
    menu(stdscr, "Okay", title=f"More than one server at U{rackU}\n{serversAtU}")
  #if we did not find a server
  if len(serversAtU) == 0:
    foundOld = True
    if hardware == "":
      hardware = menu(stdscr, list(HWTypes.keys()), "Select hardware")
    if owner == "":
      owner = prompt(stdscr, "Infrastructure" , title="Enter Project Owner:")
    if project == "":
      if owner == "Infrastructure":
        project = prompt(stdscr, "Infrastructure", title="Enter project")
      else:
        project = prompt(stdscr, "", title="Enter project")
  #if we did find a server (or two) at rackU
  else:
    oldFile = serversAtU[-1]
    importData = readConfigFile(oldFile)
    hardware = importData['Hardware'].strip()
    owner = importData['owner'].strip()
    project = importData['project'].strip()
    serial = importData['sn'].strip()
    note = importData['notes'].strip()
    powerState = (importData['powered'].strip() == "True")

  if "]" in hardware:
    hardware_name = hardware.split("]")[-1].strip()
  else:
    hardware_name = hardware

  stdscr.refresh()
  selectedIndex = 0
  c = ''

  while True:
    #key left right = change u by 1u
    if c == "KEY_LEFT":
      rackU = str(int(rackU) + 1)
      return
    if c == "KEY_RIGHT":
      rackU = str(int(rackU) - 1)
      return
    if c == "KEY_UP" and selectedIndex < 6:
      selectedIndex = selectedIndex + 1
      debug(str(selectedIndex))
    elif c == "KEY_DOWN" and selectedIndex > 0:
      selectedIndex = selectedIndex - 1
    elif c == "KEY_BACKSPACE":
      if len(serial) > 0:
        serial = serial[:-1]
        stdscr.clear()
        stdscr.refresh()
      c = ""
      continue
    elif c == "\n":
      if serial != "" and selectedIndex == 0:

        stdscr.clear()
        stdscr.refresh()
        saveConfig(sn=serial ,serverRoom=lab,rack=rack, rackU=rackU, project=project, owner=owner, IP='', Type=hardware, note=note, powerOn=powerState)
        if oldFile != "" and serial not in oldFile:
          debug("delete " + oldFile)
          os.remove(oldFile)
        else:
          debug("KEEPING" + oldFile)
          debug(serial)
        spacing = HWTypes[hardware][0]#int(rackU)-int(nextU)
        rackU = str(int(rackU) - int(spacing))
        return
      #change hardware
      if selectedIndex == 1:
        selectedIndex = 0
        note = ""
        hardware = menu(stdscr, list(HWTypes.keys()), "Select hardware")
        if "]" in hardware:
          hardware_name = hardware.split("]")[-1].strip()
        else:
          hardware_name = hardware
      elif selectedIndex == 2:
        selectedIndex = 0
        project = prompt(stdscr, project , title="Edit Project (Blank = Infrastructure):")
        owner = prompt(stdscr, owner , title="Edit Project Owner (Blank = Infrastructure):")
        if project == "":
          project = "Infrastructure"
        if owner == "":
          owner = "Infrastructure"
      elif selectedIndex == 3:
        selectedIndex = 0
        rackU = prompt(stdscr, str(rackU) , title="Enter Rack U?")
        #nextU = prompt(stdscr, "" , title="Enter next U to be scaned")
        direction = menu(stdscr, "Top Down","Bottom Up" , title="Enter scanning direction")
        spacing = HWTypes[hardware][0]#int(rackU)-int(nextU)
        if direction == "Bottom Up":
          spacing = spacing * -1
      elif selectedIndex == 4:
        selectedIndex = 0
        note = prompt(stdscr, note , title="Edit Note?")
      elif selectedIndex == 5:
        powerState = not powerState
      elif selectedIndex == 6:
        html = createHtml()
        with open("./index.html", "w") as fh:
          fh.write(html)
        menu(stdscr, "Okay", title="Updated ./index.html")
        sys.exit()
      c = ''
      continue
      
    else:
      if len(c) != 1:
        debug("Error reading key")
        c = ""
      serial = serial + c
    

    #draw edit hardware
    if selectedIndex == 1:
      stdscr.move(int(screenSize[0]/2) -1,0)
      stdscr.addstr(f"[x] Edit: {hardware_name}" + "\n",curses.color_pair(7))
    else:
      stdscr.move(int(screenSize[0]/2) -1,0)
      stdscr.addstr(f"[ ] {hardware_name}" + "\n",curses.color_pair(7))
    #draw edit project
    if selectedIndex == 2: 
      stdscr.move(int(screenSize[0]/2) -2,0)
      stdscr.addstr(f"[x] Edit: {project}/{owner}" + "\n",curses.color_pair(7))
    else:
      stdscr.move(int(screenSize[0]/2) -2,0)
      stdscr.addstr(f"[ ] {project}/{owner}" + "\n",curses.color_pair(7))
    #draw edit rackspace
    if selectedIndex == 3:
      stdscr.move(int(screenSize[0]/2) -3,0)
      stdscr.addstr(f"[x] Edit: {rack} {rackU}" + "\n",curses.color_pair(7))
    else:
      stdscr.move(int(screenSize[0]/2) -3,0)
      stdscr.addstr(f"[ ] {rack} {rackU}" + "\n",curses.color_pair(7))
    #draw edit note part
    if selectedIndex == 4:
      stdscr.move(int(screenSize[0]/2) -4,0)
      if note == "":
        stdscr.addstr("[x] Enter note",curses.color_pair(7))
      else:
        stdscr.addstr(f"[x] Edit: {note}",curses.color_pair(7))
    else:
      stdscr.move(int(screenSize[0]/2) -4,0)
      if note == "":
        stdscr.addstr("[ ] Enter note" + "\n",curses.color_pair(7))
      else:
        stdscr.addstr(f"[ ] Note: {note}",curses.color_pair(7))
    
    if selectedIndex == 5:
      if powerState:
        txt = "[x] Hardware Powered"
      else:
        txt = "[x] Hardware Off"
      stdscr.move(int(screenSize[0]/2) - 5,0)
      stdscr.addstr(txt + "\n",curses.color_pair(1))
      stdscr.move(int(screenSize[0]/2) - 1,0)
      #stdscr.addstr(serial, curses.color_pair(1))
    else:
      if powerState:
        txt = "[ ] Hardware Powered"
      else:
        txt = "[ ] Hardware Off"
      stdscr.move(int(screenSize[0]/2) - 5,0)
      stdscr.addstr(txt + "\n",curses.color_pair(7))
    
    #draw exit part
    if selectedIndex == 6:
      txt = "[x] Exit"
      stdscr.move(int(screenSize[0]/2) - 6,0)
      stdscr.addstr(txt + "\n",curses.color_pair(1))
      stdscr.move(int(screenSize[0]/2) + 1,0)
      #stdscr.addstr(serial, curses.color_pair(1))
    else:
      txt = "[ ] Exit" 
      stdscr.move(int(screenSize[0]/2) - 6,0)
      stdscr.addstr(txt + "\n",curses.color_pair(7))
    #draw serial part
    if not foundOld:
      prefix = "Editing"
    else:
      prefix = "Adding"
      
    if selectedIndex == 0:
      txt = "[x] "+prefix+" '" + hardware_name + "' in " + str(rack) + " U" + str(rackU) + " with serial: " 
      stdscr.move(int(screenSize[0]/2),0)
      stdscr.addstr(txt + "\n",curses.color_pair(1))
      stdscr.move(int(screenSize[0]/2) + 1,0)
      stdscr.addstr(serial, curses.color_pair(1))
    else:
      txt = "[ ] "+prefix+" '" + hardware_name + "' in " + str(rack) + " U" + str(rackU) + " with serial: " 
      stdscr.move(int(screenSize[0]/2),0)
      stdscr.addstr(txt + "\n",curses.color_pair(7))
      
    c = stdscr.getkey()
    debug("Entered" + str(c))
    



#arg1 = stdscr
#arg2/3/4... = option/List of options
#title = Message to show at top of screen. 
def menu(*args, title="", position="mid"):
  if len(args) < 2:
    return 1
  
  stdscr = args[0]
  options = args[1:]
  stdscr.clear()
  
  loadConfig()
  
  
  if isinstance(options[0], (list,)):
    options = options[0]
  debug(str(options))
  screenSize = stdscr.getmaxyx()  
  selectedIndex = 0
  
  if title != "":
    stdscr.move(0,0)
    stdscr.addstr(title,curses.color_pair(7))
    
  #find longest option
  longestWord = 0
  for option in options:
    if len(option) > longestWord:
      longestWord = len(option)
  while True:
    if position == "mid":
      printStart = int(screenSize[0]/2) - int(len(options)/2)
    elif position == "bot":
      printStart = int(screenSize[0]) - int(len(options))
      
    for optionIndex in range(0,len(options)):
      debug(str((int(printStart),int(screenSize[1]/2))))
      stdscr.move(int(printStart),int(screenSize[1]/2) - int(longestWord/2))
      if optionIndex == selectedIndex:
        stdscr.addstr("[*]" + str(options[optionIndex]),curses.color_pair(1))
      else: 
        stdscr.addstr("[ ]" + str(options[optionIndex]),curses.color_pair(4))
      printStart = printStart + 1
    stdscr.refresh()
    #get new KEY
    c = stdscr.getkey()
    debug(str(c))
    if c == "KEY_DOWN" and selectedIndex < len(options) -1:
      selectedIndex = selectedIndex + 1
    debug(str(selectedIndex))
    if c == "KEY_UP" and selectedIndex > 0:
      selectedIndex = selectedIndex - 1
    if c == "\n":
      stdscr.clear()
      stdscr.refresh()
      return options[selectedIndex]


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
  


if __name__ == '__main__':
    curses.wrapper(main)

