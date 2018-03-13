from libbhyve.vm import VM
from libbhyve.config import *
from flask import Flask, jsonify, request
from flask_restful import reqparse, Resource, Api
from functools import wraps
from os.path import isfile
from os import listdir
from time import sleep
import json
import subprocess
import sys
import traceback
app = Flask(__name__)
api = Api(app)

def load_vm(f):
    @wraps(f)
    def wrapper(vm_name, *args, **kwargs):
        return f(VM(vm_name))

    return wrapper


@app.route('/')
def root():
    return 'bapi root'

@app.route('/vm/', methods=['GET', 'POST'])
def vms_ep():
    """ """
    if request.method == 'POST':
        try:
            myvm = VM(request.json)
            myvm.create()
            myvm.save()
            return jsonify({"status": myvm.status()}), 200 
        except subprocess.CalledProcessError, e:
            return jsonify({"failed": '%s' % e}), 200 
    elif request.method == 'GET':
        return jsonify({'vms': listdir(VM_DIR)}), 200

@app.route('/vm/<vm_name>/dump', methods=['GET'])
@load_vm
def vm_dump(vm):
    return jsonify(vm.dump_to_dict()), 200 
    
@app.route('/vm/<vm_name>', methods=['DELETE', 'GET', 'PATCH', 'POST'])
@load_vm
def vm_ep(vm):
    if request.method == 'GET':
        return jsonify({"state": vm.status()}), 200
    elif request.method == 'PATCH':
        vm.load_from_dict(request.json)
        vm.save()
        vm.create()
        return jsonify({'state': 'vm modified'}) 
    elif request.method == 'POST':
        if request.json['action']: 
            if request.json['action'] == 'start':
                try:
                    vm.start()
                    # needs a little time for the process to spin up
                    sleep(1)
                    return jsonify({"state": vm.status()}), 200
                except OSError as e:
                    return jsonify({"error": str(e), "state": vm.status()}), 500
                     
            elif request.json['action'] == 'stop':
                vm.stop()
                return jsonify({"state": vm.status()}), 200
            elif request.json['action'] == 'restart':
                vm.restart()
                sleep(1)
                return jsonify({"state": vm.status()}), 200

    elif request.method == 'DELETE':
        vm.delete()
        return jsonify({'status': 'deleted'}), 202

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8001)
