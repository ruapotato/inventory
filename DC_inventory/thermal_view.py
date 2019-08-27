from flask import Flask, request, Response
#app = Flask(__name__)
from . import DC_inventory
from . env_auth import *
from . configs import *
from . html import *


@DC_inventory.route("/admin/thermal/<lab>/index.html")
@requires_auth
def thermal_lab(lab):
    return createHtml(filterLab=lab, thermal=True)

