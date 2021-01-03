#!/usr/bin/python3
from vedo import load, show

import math
import stl
from stl import mesh
import numpy
import os
import re

#from DC_inventory.env_auth import loadEnv
from  DC_inventory.configs import *

script_path = os.path.dirname(os.path.realpath(__file__))
mesh_tmp = f"{script_path}/mesh_tmp/"

Target_lab = "Example Lab"
USED_COLORS = {}
USER_COLORS = ['0f4bff','c30fff','ff870f','ff0f87']
colorIndex = 0

#Setup STLs
u1_item = mesh.Mesh.from_file(f'{script_path}/mesh/1U.stl')
u2_item = mesh.Mesh.from_file(f'{script_path}/mesh/2U.stl')
#for rack in allRacks:

#Thanks https://stackoverflow.com/a/62083599/5282272
def hex_to_rgb(hx, hsl=False):
    """Converts a HEX code into RGB or HSL.
    Args:
        hx (str): Takes both short as well as long HEX codes.
        hsl (bool): Converts the given HEX code into HSL value if True.
    Return:
        Tuple of length 3 consisting of either int or float values.
    Raise:
        ValueError: If given value is not a valid HEX code."""
    if re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$').match(hx):
        div = 255.0 if hsl else 0
        if len(hx) <= 4:
            return tuple(int(hx[i]*2, 16) / div if div else
                         int(hx[i]*2, 16) for i in (1, 2, 3))
        return tuple(int(hx[i:i+2], 16) / div if div else
                     int(hx[i:i+2], 16) for i in (1, 3, 5))
    else:
        raise ValueError(f'"{hx}" is not a valid HEX code.')


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
    global u1_item
    #Base dist on standerd 1u size
    minx, maxx, miny, maxy, minz, maxz = find_mins_maxs(u1_item)
    w = maxx - minx
    l = maxy - miny
    h = maxz - minz
    
    _copy = mesh.Mesh(obj.data.copy())
    if z != 0:
        translate(_copy, h, h / 5., z, 'z')
    if x != 0:
        translate(_copy, w, w / 5., x, 'x')
    if y != 0:
        translate(_copy, l, l / 5., y, 'y')
    return _copy


def hw_to_stl(name):
    global u1_item
    global u2_item
    #TODO
    u_size = int(HWTypes[hardware][0])
    if u_size == 1:
        return u1_item
    else:
        return u2_item

def draw_item(stl, rack, rack_u, u_size):
    offset = u_size - 1
    return obj_at(stl, int(rack), 0, int(rack_u) - offset)

#setup letters
STL_LETTERS = {}
for letter in "":
    STL_LETTERS[letter] = mesh.Mesh.from_file(f"{script_path}/letters/{letter}.stl")



#allRacks = list(LabSpace[lab].keys())
server_room = {}
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
            if "notes" in rack_item:
                notes       = rack_item['notes']
            else:
                notes = ""
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
            

            #server_room.append(draw_item(stl_to_use, rack_index, rack_u, u_size))
            server_room[sn] = [draw_item(stl_to_use, rack_index, rack_u, u_size), item_color]





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
#draw server room parts:
stl_color = {}
simple_list = []
for item in server_room:
    print(item)
    data = server_room[item]
    print(data)
    render = data[0]
    color = data[-1]
    name = f"{mesh_tmp}{item}.stl"
    render.save(name, mode=stl.Mode.AUTOMATIC)
    stl_color[name] = color
    simple_list.append(name)

acts = []
for stl_file in simple_list:
    acts.append(load(stl_file))
    color = stl_color[stl_file]
    print(f"{color}")
    color = hex_to_rgb(f"#{color}")
    acts[-1].color(color).scale(1).pos(1,2,3)
    print(f"{stl_file} {color}")

show(acts)
exit()
    #item.save("")
    #mesh_tmp

#render = mesh.Mesh(numpy.concatenate([server.data for server in server_room]))
#render.save('server_room.stl', mode=stl.Mode.AUTOMATIC)


filenames = ['server_room.stl', f'{script_path}/mesh/test.stl']
acts = load(filenames) # list of Mesh(vtkActor)
acts[0].color([1.0,0,1.0]).scale(1).pos(1,2,3)
show(acts)
