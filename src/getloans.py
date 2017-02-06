import pandas as pd
import numpy as np
import requests
import time
from pandas.io.json import json_normalize
import json
import os
import glob
import netrc

import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
#try:
#    import http.client as http_client
#except ImportError:
    # Python 2
#    import httplib as http_client
#http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

with open('config/config.json', 'r') as f:
    config = json.load(f)

base_url = config['baseUrl']  + config['apiVer'];
info = netrc.netrc()
config['investorId'], account, config['apiKey'] = info.authenticators("api.lendingclub.com")
acct_suffix_url = '/accounts/' + config['investorId'];
headers = {'Authorization': config['apiKey'], 'Accept': 'application/json', 'Content-Type': 'application/json'}

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



def parent_order():
	res = '{ \n'
	res += '"aid":' + config['investorId'] + ',\n'
	res += '"orders":[\n'
	return res

def gen_order( portf,loan ):
	res = '{ '
	res += '"loanId":' + str(loan['id'].item()) + ',\n'
	res += '"requestedAmount":25.0,\n' 
	res += '"portfolioId":'+ portf + '\n}\n'
	return res


def add_order( po,portf,loan ):
	if (po=="") :
		po = parent_order()
	po += gen_order(portf,loan)
	return po

def all_orders(portf,loans):
	po = parent_order()
	for index, row in loans.iterrows():
		po += gen_order(portf,row)
		if (index<len(loans)-1):
			po += ',\n'
	po += '	]'
	po += '}'
	return po

dirname = "data/pandas/" + time.strftime("%Y.%m.%d")
release_tm = time.strftime("%I%p_%M:%S");
if not os.path.exists(dirname):
    os.makedirs(dirname)

session = requests.Session()
session.trust_env = False
sum_url = get_url(1,'summary');
print sum_url
print headers
r = session.get(sum_url, headers=headers)
print r
lsum_cols = ['term','intRate','fundedAmount','loanAmount','installment','purpose','annualInc','dti','empLength']
loanlist_url = get_url(0,'loans/listing');
loan_list = session.get(loanlist_url, headers=headers)
mydf = json_normalize(loan_list.json()['loans'])

newlisted_f = "newlisted_" + release_tm + ".pkl";
mydf.to_pickle(dirname + '/' + newlisted_f) 

for pf in config['portfolios']:
	port_match = mydf.query(pf['query'])
	portmatch_f = dirname + "/" + pf['portfolioName'].lower() + "_" + release_tm + ".pkl";
	if not port_match.empty:
		port_match.to_pickle(portmatch_f) 
	else:
		open(portmatch_f, 'a').close()

