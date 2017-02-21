import json
import os
import glob

import lcaccount

default_config_file = 'config/config.json'

def load_config_file(cfgfile=default_config_file):
	with open(cfgfile, 'r') as f:
		return json.load(f)

def load_config():
	cfg = load_config_file()
	cfg['investorId'], account, cfg['apiKey'] = lcaccount.load_account()
	return cfg


