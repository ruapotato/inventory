import os
from flask import Flask, request, Response

from . import DC_inventory


scriptPath = os.path.dirname(os.path.realpath(__file__))
#change scriptPath to be the main folder/up one dir
scriptPath = scriptPath.split('DC_inventory')[0]

configFiles = scriptPath + "configs/"


@DC_inventory.route('/notes/<lab>/<rack>/<serial>/', methods=['GET', 'POST'])
def submit_notes(lab, rack, serial):
    notes_file = f"{configFiles}{lab}/{rack}/{serial}.notes"
    if request.method == 'POST':
        notes = request.form.get('notes')
        with open(notes_file, 'w+') as fh:
            fh.write(notes)
        return f"<script type='text/javascript'>window.close() ;</script> "
    else:
        notes = ""
        if os.path.exists(notes_file):
            with open(notes_file) as fh:
                lines = fh.readlines()
            
            for line in lines:
                notes = notes + line
        
        return f'''
        <!doctype html>
        <title>Notes</title>
        <form method="POST">
        <textarea rows="4" cols="50" name="notes">{notes}</textarea>
        <input type="submit" value="Submit"><br>
        </form>'''
