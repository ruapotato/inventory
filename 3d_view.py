#!/usr/bin/python3
import math
import stl
from stl import mesh
import numpy
import os

#from DC_inventory.env_auth import loadEnv
from  DC_inventory.configs import *

script_path = os.path.dirname(os.path.realpath(__file__))

Target_lab = "Example Lab"
USED_COLORS = {}
USER_COLORS = ['0DFFC6','0FFF27','ffffff','ffff00']
colorIndex = 0

#Setup STLs
server = mesh.Mesh.from_file(f'{script_path}/mesh/test.stl')

#for rack in allRacks:

# find the max dimensions, so we can know the bounding box, getting the height,
# width, length (because these are the step size)...
def find_mins_maxs(obj):
    minx = obj.x.min()
    maxx = obj.x.max()
    miny = obj.y.min()
    maxy = obj.y.max()
    minz = obj.z.min()
    maxz = obj.z.max()
    return minx, maxx, miny, maxy, minz, maxz


def translate(_solid, step, padding, multiplier, axis):
    if 'x' == axis:
        items = 0, 3, 6
    elif 'y' == axis:
        items = 1, 4, 7
    elif 'z' == axis:
        items = 2, 5, 8
    else:
        raise RuntimeError('Unknown axis %r, expected x, y or z' % axis)

    # _solid.points.shape == [:, ((x, y, z), (x, y, z), (x, y, z))]
    _solid.points[:, items] += (step * multiplier) + (padding * multiplier)

def obj_at(obj, x,y,z):
    global server
    #Base dist on standerd server size
    minx, maxx, miny, maxy, minz, maxz = find_mins_maxs(server)
    w = maxx - minx
    l = maxy - miny
    h = maxz - minz
    
    _copy = mesh.Mesh(obj.data.copy())
    if z != 0:
        translate(_copy, h, h / 10., z, 'z')
    if x != 0:
        translate(_copy, w, w / 10., x, 'x')
    if y != 0:
        translate(_copy, l, l / 10., y, 'y')
    return _copy


def hw_to_stl(name):
    global server
    #TODO
    return server

def draw_item(stl, rack, rack_u):
    return obj_at(stl, int(rack), 0, int(rack_u))

#setup letters
STL_LETTERS = {}
for letter in "":
    STL_LETTERS[letter] = mesh.Mesh.from_file(f"{script_path}/letters/{letter}.stl")



#allRacks = list(LabSpace[lab].keys())
server_room = []
lab_racks = LabSpace[Target_lab]
#labs = loadLabData()
lab_data = labs[Target_lab]
for rack in lab_racks:
    if rack in lab_data:
        print(f"Rack: {rack}")
        print(f"keys: {lab_data[rack].keys()}")
        stuff_in_rack = lab_data[rack]
        for server_ID in stuff_in_rack:
            rack_item = stuff_in_rack[server_ID]


            if 'BC' in rack_item:
                bc = rack_item['BC']
            else:
                bc = ""
            sn          = rack_item['sn']
            rack_name   = rack_item['rack']
            rack_u      = rack_item['rackU']
            project     = rack_item['project']
            owner       = rack_item['owner']
            hardware    = rack_item['Hardware']
            notes       = rack_item['notes']
            powered     = rack_item['powered'] == "True"
            #rip out number from rack name
            rack_index =  int("".join([i for i in rack_name if i.isdigit()]))
            
            #Setup color
            ownerKey = project + owner
            if ownerKey not in USED_COLORS:
                USED_COLORS[ownerKey] = USER_COLORS[colorIndex]
                colorIndex = colorIndex + 1
                if colorIndex >= len(USER_COLORS):
                    colorIndex = 0
            item_color = USED_COLORS[ownerKey]
            
            sort_hw_name = hardware.split("]")[-1].strip()
            
            #lookup U size
            u_size = int(HWTypes[hardware][0])
            
            #setup lable to display on hardware
            lable = f"{sort_hw_name}:{project}"
            
            print(f"Item: Rack {rack_index} U{rack_u} size:{u_size}U color: {item_color}")
            print(lable)
            
            stl_to_use = hw_to_stl(hardware)
            

            #stack 1
            server_room.append(draw_item(stl_to_use, rack_index, rack_u))
            #server_room.append(obj_at(server, 1,1,1))
            #draw_item(stl, rack, rack_u):
            #TODO rack_index = something[rack_name]
            #TODO item_color = something[hardware]
            #TODO item_size  =
            




# Using an existing stl file:
#main_body = mesh.Mesh.from_file('test.stl')

"""
minx, maxx, miny, maxy, minz, maxz = find_mins_maxs(main_body)
w = maxx - minx
l = maxy - miny
h = maxz - minz

server_room = []
#stack 1
server_room.append(obj_at(STL_LETTERS['A'], 1,1,1))
server_room.append(obj_at(server, 1,1,1))
server_room.append(obj_at(server, 1,1,2))
server_room.append(obj_at(server, 1,1,3))
server_room.append(obj_at(server, 1,1,4))
server_room.append(obj_at(server, 1,1,5))

#stack 2
server_room.append(obj_at(STL_LETTERS['A'], 1,2,1))
server_room.append(obj_at(server, 1,2,1))
server_room.append(obj_at(server, 1,2,2))
server_room.append(obj_at(server, 1,2,3))
#server_room.append(obj_at(server, 3,3,3))
#copies = copy_obj(main_body, (w, l, h), 1, 1, 2)
"""


"""
_copy = mesh.Mesh(main_body.data.copy())
translate(_copy, h, h / 10., 1, 'z')
server_room.append(_copy)

_copy2 = mesh.Mesh(main_body.data.copy())
translate(_copy2, h, h / 10., 3, 'z')
server_room.append(_copy2)

_copy3 = mesh.Mesh(main_body.data.copy())
translate(_copy, h, h / 10., 4, 'z')
server_room.append(_copy3)
"""
render = mesh.Mesh(numpy.concatenate([server.data for server in server_room]))
render.save('server_room.stl', mode=stl.Mode.AUTOMATIC)

from vedo import load, show
filenames = ['server_room.stl', f'{script_path}/mesh/test.stl']
acts = load(filenames) # list of Mesh(vtkActor)
acts[0].color([1.0,0,1.0]).scale(1).pos(1,2,3)
show(acts)
