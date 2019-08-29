import threading
import subprocess
from datetime import datetime
import time
from flask import Flask, request, Response
#app = Flask(__name__)
from . import DC_inventory
from . env_auth import *
from . configs import *


IPMI_WORKING = {}
IPMI_BROKEN = {}
ipmiConfigs = {}
ipmiWaitTime = 60
#tests run on chassis status
IPMI_should_be_false = ['Power Overload', 'Main Power Fault', 'Power Control Fault', 'Drive Fault', 'Cooling/Fan Fault']

@DC_inventory.route('/admin/ipmisetup/<lab>/<rack>/<sn>/<ip>/<user>/<passwd>')
@requires_auth
def ipmiAdd(lab, rack, sn, ip, user, passwd):
    returnHtml = ""
    fullPath = f'{scriptPath}/configs/{lab}/{rack}/{sn}.ipmi'
    fileStuff = f"{ip}:{user}:{passwd}"
    with open(fullPath, 'w') as fh:
        fh.write(fileStuff)
    return(returnHtml)


@DC_inventory.route('/admin/IPMI/<lab>/<rack>/<sn>')
@requires_auth
def ipmiHtml(lab,rack,sn):
    returnHtml = """
    IP: <input id=ipmiIP></input> <br>
    User: <input id=ipmiUser></input> <br>
    Password: <input type="password" id=ipmiPasswd></input> <br>"""
    
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

def IPMI_pull_hw(server, config):
    hw_log_file = config[:-5] + ".hw"
    cmd = IPMI_cmd_str(server) + "fru"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    #find serial number
    mfg_date = ""
    product = ""
    serial = ""
    part_number = ""
    prod_man = ""


    if p.returncode == 0:
        out = out.decode('UTF-8')
        for line in out.split('\n'):
            line = line.strip()
            #only read frist block
            if line == "":
                break
            if line.startswith("Board Mfg Date"):
                mfg_date = line.split(":")[-1].strip()
            if line.startswith("Board Mfg") or line.startswith("Board Manufacturer"):
                prod_man = line.split(":")[-1].strip()
            if line.startswith("Board Product") or line.startswith("Product Name"):
                product = line.split(":")[-1].strip()
            if line.startswith("Board Serial"):
                serial = line.split(":")[-1].strip()
            if line.startswith("Board Part Number"):
                part_number = line.split(":")[-1].strip()
        
        hw_log = f"""prod={product}\nserial={serial}\nmfg_date={mfg_date}\npart_number={part_number}\nprod_man={prod_man}"""
        with open(hw_log_file, 'w') as fh:
            fh.write(hw_log)

    
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
        #IPMI working
        if config in IPMI_BROKEN:
            del(IPMI_BROKEN[config])
        IPMI_WORKING[config] = out.decode('UTF-8')
        IPMI_write_log(config, out.decode('UTF-8'), IPMI_health_check(server))
        IPMI_pull_hw(server, config)
        
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

