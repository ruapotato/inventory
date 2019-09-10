import os
from functools import wraps
from flask import request, Response

#used for admin login and env loading
scriptPath = os.path.dirname(os.path.realpath(__file__))
#change scriptPath to be the main folder/up one dir
scriptPath = scriptPath.split('DC_inventory')[0]


def loadEnv():
    HWTypes = {} #{'name': [U_size, Power, color]
    LabSpace = {}
    colorMap = {}
    USER_COLORS = ""
    users = {}
    categorys = []

    with open(scriptPath + "/env.config") as fh:
        for line in fh.readlines():
            line = line.strip()
            if line.startswith('#') or line.strip() == "":
                continue
            #add HWTypes
            #[TYPE] <name>:<U space>#color
            if line.startswith('['):
                name, size, power = line.split(":")
                HWTypes[name] = [size, power]
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
    
    #return crap
    return [HWTypes,LabSpace,colorMap,USER_COLORS,users,categorys]

    
#Thanks: http://flask.pocoo.org/snippets/8/
def check_auth(username, password):
    HWTypes,LabSpace,colorMap,USER_COLORS,users,categorys = loadEnv()
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
