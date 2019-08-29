from flask import Flask, request, Response
#app = Flask(__name__)
from . import DC_inventory
from . env_auth import *
from . configs import *
from . html import *


@DC_inventory.route("/admin/power/<lab>/index.html")
@requires_auth
def power_lab_admin(lab):
    return createHtml(filterLab=lab, power_view=True)

@DC_inventory.route("/power/<lab>/index.html")
def power_lab(lab):
    return createHtml(filterLab=lab, power_view=True, admin=False)
