import json
import os
import glob
import netrc

with open('config/config.json', 'r') as f:
    config = json.load(f)

base_url = config['baseUrl']  + config['apiVer'];
info = netrc.netrc()
config['investorId'], account, config['apiKey'] = info.authenticators("api.lendingclub.com")
acct_suffix_url = '/accounts/' + config['investorId'];
myheaders = {'Authorization': config['apiKey'], 'content-type': 'application/json'}

portfolio_path = "config/portfolio/"
port_l = []
config['portfolios'] = []
for file in glob.glob(portfolio_path + "*.json"):
	port_name = (os.path.splitext(os.path.basename(file))[0]).upper();
	with open(file, 'r') as f:
		cur_port = json.load(f)
		config['portfolios'].append(cur_port)

def get_url( acct,action ):
	if (acct) :
		suf = acct_suffix_url
	else :
		suf = ''
	return base_url + suf + "/" + action;
