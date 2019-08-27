import os
import subprocess

scriptPath = os.path.dirname(os.path.realpath(__file__))
#change scriptPath to be the main folder/up one dir
scriptPath = scriptPath.split('DC_inventory')[0]

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


#Thanks https://stackoverflow.com/a/136280
def tail(f, n=12):
    proc = subprocess.Popen(['tail', '-n', str(n), f], stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
    return lines
