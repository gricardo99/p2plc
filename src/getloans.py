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
headers = {'Authorization': config['apiKey'], 'Accept': 'application/json', 'Content-Type': 'application/json', 'X-LC-LISTING-VERSION': '1.1'}

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
        res += '\t"aid":' + config['investorId'] + ',\n'
        res += '\t"orders":[\n'
        return res

def gen_order( portf,loan ):
        res = '\t{ '
        res += '\t"loanId":' + str(loan[['id']].item()) + ',\n'
        res += '\t"requestedAmount":25.0,\n' 
        res += '\t"portfolioId":'+ portf + '\n\t}'
        return res


def all_orders(portf_name,loans,max_buy):
        po = parent_order()
        for p in config['portfolios']:
                if (p['portfolioName']==portf_name):
                        portf_id = p['portfolioId']
                        break
        for index, row in loans.iterrows():
                po += gen_order(portf_id,row)
                if (index<len(loans)-1) and (index<max_buy-1):
                        po += ',\n'
                else:
                        po += '\n'
                if (index<max_buy):
                        break
        po += '\t]\n'
        po += '}'
        return po

cur_date = time.strftime("%Y.%m.%d")
release_tm =  time.strftime("%I%p_%M:%S")

dirname = "data/pandas/" + cur_date
if not os.path.exists(dirname):
    os.makedirs(dirname)

logname = "log/" + cur_date
if not os.path.exists(logname):
    os.makedirs(logname)


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=logname + '/getloans.log')



session = requests.Session()
session.trust_env = False
#sum_url = get_url(1,'summary');
#print sum_url
#print headers
#r = session.get(sum_url, headers=headers)
#print r
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
		order_payload_name = "log/" + cur_date + "/" + pf['portfolioName'].lower() + "_orders.json"
		order_resp_name = "log/" + cur_date + "/" + pf['portfolioName'].lower() + "_resp.json"
		logging.debug("order_payload_name:%s",order_payload_name)
		logging.debug("order_resp_name:%s",order_resp_name)
		if (not os.path.exists(order_payload_name)):
			pyld_f = open(order_payload_name, 'w')
			resp_f = open(order_resp_name, 'w')
			logging.debug("created order and resp files. portfolio:%s",pf['portfolioName']);
			port_match.sort(['intRate','dti'],ascending=[False,True],inplace=True)
			port_match.reset_index(drop=True, inplace=True)
			order_url = get_url(1,'orders')
			logging.debug("order_url:%s",order_url)
			payload = all_orders(pf['portfolioName'],port_match,1)
			logging.debug("payload:%s",payload)
			json.dump(payload,pyld_f)
			#ordresp = session.post(order_url, headers=headers, data=json.dump(payload))
		else:
			logging.debug("skipping orders for portfolio:%s",pf['portfolioName']);
		port_match.to_pickle(portmatch_f) 
		logging.debug("written pickle to %s",portmatch_f)
	else:
		logging.debug("skipping orders, no matches for portfolio:%s",pf['portfolioName']);
		open(portmatch_f, 'a').close()

