#!/usr/bin/env python

import time
import os
import json
import argparse
import sys

from flask import Flask
from flask import Response
from flask import request
from flask import abort
from werkzeug.utils import secure_filename

import matlab.engine

args = {}

app = Flask(__name__)
@app.route('/matlab/<action>', methods=['POST'])
def handle_matlab(action):
	print
	print '***************************************'
	print '** Request Recieved'

	print '** Identifying Request'
	if request.form["whoisthis"] != "who knows":
		print(" ** Unauthorized request")
		abort(403)

	print '** Saving uploads'
	saved_files = save_upload_files(request.files)

	print '** Analyzing files'
	result = matlab_analyse(action, saved_files)
	print '** Analysis completed'
	
	resp = Response(result)
	resp.headers['Access-Control-Allow-Origin'] = args['webapp_host']
    
	return resp 
    
def save_upload_files(uploadfile):
    a_file = uploadfile['uploadfile']
    file_path = 'uploads'
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    time_stamp = str(time.time())
    file_name = time_stamp + '-' + secure_filename(a_file.filename)
    
    temp_file = os.path.join(file_path, file_name)
    a_file.save(temp_file)

    return temp_file

def matlab_analyse(action, files):
    eng = matlab.engine.start_matlab()
    matlab_func = getattr(eng, action)
    
    result = dict()
    try:
    	result = matlab_func(files)
    except Exception as e:
        print e
        msg = "Error while excuting matlab script" 
        result['error'] = msg
    
    try:
        result = json.dumps(result)
    except Exception as e:
        print e
        msg = "Results from the matlab script is not JSON serializable, please check" 
        result = '{"error":"' + msg + '"}'
    return result

def arguments_handling(ori_args):
	with open('args.json') as arg_file:
		arg_options = json.load(arg_file)
		arg_file.close()
	
	parser = argparse.ArgumentParser()
	for option in arg_options.values():
		parser.add_argument(option['abbr'], option['full'], help=option['description'], nargs='?')
	parsed = vars(parser.parse_args(ori_args))

	parsed_args = {}
	for option in arg_options:
		parsed_args[option] = arg_options[option]['default']
		if parsed[arg_options[option]['name']]:
			parsed_args[option] = parsed[arg_options[option]['name']]

			if option == 'webapp_host' and parsed[arg_options[option]['name']] == 'all':
				parsed_args[option] = '*'
	
	return parsed_args

if __name__ == "__main__":
	args = arguments_handling(sys.argv[1:])
	print 'use -h to see more options'

	print 'handling requests from ' + args['webapp_host']
	app.run(host=args['listening_on'], port=args['my_port'], threaded=True)