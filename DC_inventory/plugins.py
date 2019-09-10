from flask import Flask, request, Response
#app = Flask(__name__)
from . import DC_inventory
from . env_auth import *
from . configs import *
from . html import *

import re

#extra_menu_items = ['name':"url"]
