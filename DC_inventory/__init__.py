from flask import Blueprint
DC_inventory = Blueprint('DC_inventory', __name__)

from .DC_view import *
from .IPMI import *
from .thermal_view import *
from .power_view import *
