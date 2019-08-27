#!/usr/bin/python3
import threading

from DC_inventory import *
app = Flask(__name__)
app.register_blueprint(DC_inventory)


def getIP():
    import socket
    #Thanks: https://stackoverflow.com/a/1267524/5282272
    return (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]


#starup IPMIlistener
t = threading.Thread(target=IPMI_listener)
t.daemon = True
t.start()


#run with gevent in production
#needs root
if __name__ == '__main__':
    import gevent.pywsgi

    #app_server = gevent.pywsgi.WSGIServer((getIP(), 80), app)
    app_server = gevent.pywsgi.WSGIServer((getIP(), 443), app, keyfile=scriptPath + '/key.pem', certfile=scriptPath + '/cert.pem')

    app_server.serve_forever()
