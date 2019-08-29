import os
from . env_auth import loadEnv
from . css import CSS
from . configs import *

HWTypes,LabSpace,colorMap,USER_COLORS,users,categorys = loadEnv()
scriptPath = os.path.dirname(os.path.realpath(__file__))
#change scriptPath to be the main folder/up one dir
scriptPath = scriptPath.split('DC_inventory')[0]


powerOffColor = "#cc2900"
InfrastructureColor = "#8e13c6"


USER_COLORS = ['0DFFC6','0FFF27','ffffff','ffff00']
#only used if USER_COLORS: is missing from config
colorIndex = 0
USED_COLORS = {}
users = {}
categorys = []

def dc_JS(scroll=0, admin=True, lab=""):
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
    returnHtml = "<div id=links>"
    if admin:
        start = "/admin/"
    else:
        start = "/"
    
    for lab in LabSpace.keys():
        returnHtml = returnHtml + "<div class='dropdown'>"
        returnHtml = returnHtml + f'<button class="dropbtn">{lab}</button>'
        returnHtml = returnHtml + '<div class="dropdown-content">'
        returnHtml = returnHtml + f'<a href="{start}{lab}/index.html">DC Inventory</a>'
        returnHtml = returnHtml + f'<a href="{start}thermal/{lab}/index.html">Thermal view</a>'
        returnHtml = returnHtml + f'<a href="{start}power/{lab}/index.html">Power view</a>'
        returnHtml = returnHtml + '</div></div>'
        #f"<a href='{start}{lab}/index.html'>{lab}</a>&nbsp;"
    #returnHtml = returnHtml + "<a href='#filterInput'>Search</a>"
    return returnHtml + '&nbsp;  <button id="myBtn">Open Legend</button></div>'


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
    HWTypes,LabSpace,colorMap,USER_COLORS,users,categorys = loadEnv()
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
def color_by_temp(temp):
    red_start = 25
    red_max = 36
    blue_start = 0
    blue_max = 28
    red = 0
    temp = int(temp)
    if temp == 0:
        return "888888"
    #Red value
    red_multiplier = 255/(red_max - red_start)
    if temp >= red_start:
        red = int((temp-red_start) * red_multiplier)
    if temp >= red_max:
        red = 255
    #blue value
    blue_multiplier = 155/(blue_max - blue_start)
    if temp >= blue_start and temp <= blue_max:
        blue = int((temp-blue_start) * blue_multiplier)
        blue = blue + 100
    if temp > blue_max:
        blue = 255
        print(blue)
        dimmer = (temp - blue_max)
        if dimmer > 5:
            dimmer = 5
        dimmer = dimmer * (255/5)
        blue = int(blue - dimmer)
        print(blue)
    color = str(hex(red)).split("x")[-1].zfill(2) + "00" + str(hex(blue)).split("x")[-1].zfill(2)
    return(color)

#If BLANK is true rack is used for rackname
def rack2Html(rack, size=42, BLANK=False, tooltip=False, filterLab="", thermal=False, power_view=False):
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
    
    total_power = 0
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
            #add power
            powered = server['powered']
            if powered == "True":
                hw_name = server['Hardware']
                power = int(HWTypes[hw_name][1])
            else:
                power = 0
            total_power = total_power + power

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
                #remove the oldest file:
                if os.path.getctime(bad_file1) < os.path.getctime(bad_file2):
                    debug(f'\n\n----------------------\nDuplicate entry in: {lab} {rack_name} {rackU} removing:\n{bad_file1}\nand keeping\n{bad_file2}\n------------------------')
                    #TODO remove the oldest file, This is more or less random.
                    os.remove(bad_file1)
                else:
                    debug(f'\n\n----------------------\nDuplicate entry in: {lab} {rack_name} {rackU} removing:\n{bad_file2}\nand keeping\n{bad_file1}\n------------------------')
                    #TODO remove the oldest file, This is more or less random.
                    os.remove(bad_file2)
        else:
            #error, Server not in U of rack
            debug("Error, Server out of U: " +str(rackData))
            server['project'] = "U Error: " + server['project']
            rackData[-1] = server
    
    if power_view:
        rackName = str(total_power) + " watts total " + rackName
    returnHtml = '<table class="rack" border="0" cellspacing="0" cellpadding="1">\n<tbody><tr><th width="10%">&nbsp;</th> <th width="80%">' +  str(rackName) + '</th> <th width="10%">&nbsp;</th> </tr>'
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
            if powered == "True":
                hw_name = rackData[i]['Hardware']
                power = int(HWTypes[hw_name][1])
            else:
                power = 0
            
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
            if power_view:
                name = str(power) + " watts: " + name
            #make Infrastructure purple
            if owner == "Infrastructure":
                color = InfrastructureColor.strip('#')
                ownerColor = InfrastructureColor.strip('#')
                debug("WORKING: " + color)

            #overwrite color if needed
            if thermal:
                color = color_by_temp(heat[0])
                ownerColor = color_by_temp(heat[1])
            elif 'color' in rackData[i].keys():
                color = rackData[i]['color']
            elif color == "":
                color = HWTypes[rackData[i]['Hardware']][-1]

            #powered off server have a red gradient
            if powered == "False" and not thermal:
                if owner == "Infrastructure":
                    color1 = InfrastructureColor.strip('#')
                else:
                    if 'color' in rackData[i].keys():
                        color1 = rackData[i]['color']
                    else:
                        color1 = HWTypes[rackData[i]['Hardware']][-1]

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
def createHtml(loadU=-1, loadLab="", loadRack="", lastRack={}, scroll=0, admin=True, snNA=False, filterLab="", thermal=False, power_view=False):

    if admin:
        bodyHtml = adminBODY
    else:
        bodyHtml = BODY
    #newEditBox preLoadEditBox
    if loadU < 0:
        returnHtml = CSS + dc_JS(scroll=scroll, admin=admin,lab=filterLab) + bodyHtml
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
            returnHtml = CSS + dc_JS(scroll=scroll,lab=filterLab) + bodyHtml + "<div id='editServer' display: table;>" + preLoadEditBox(allData) + "</div>"
        else:
            #we did not fine a server at U
            returnHtml = CSS + dc_JS(scroll=scroll,lab=filterLab) + bodyHtml + newEditBox(filterLab=filterLab) #I don't think this is called anymore TODO

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
                returnHtml = returnHtml + rack2Html(labs[lab][rack], size=int(LabSpace[lab][rack]), tooltip=not admin, filterLab=filterLab, thermal=thermal, power_view=power_view)
                filteredTableHtml = filteredTableHtml + rack2Table(labs[lab][rack])
            else:
                returnHtml = returnHtml + rack2Html(rack,BLANK=True, size=int(LabSpace[lab][rack]), tooltip=not admin, filterLab=filterLab, thermal=thermal, power_view=power_view)
        returnHtml = returnHtml + storageToHTML(storage)
        returnHtml = returnHtml + "\n</div>"
    returnHtml = returnHtml + "</div>" + filteredTableHtml + "</table>"
    return returnHtml + "</body>"



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




