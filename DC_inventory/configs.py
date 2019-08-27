import os

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
