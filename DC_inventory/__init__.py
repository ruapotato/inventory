from flask import Blueprint
DC_inventory = Blueprint('DC_inventory', __name__)

from .DC_view import *
from .IPMI import *
from .thermal_view import *
from .power_view import *
from .posts import *

#check for plugin file
import os
scriptPath = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(scriptPath + "/plugins.py"):
    from .plugins import *
