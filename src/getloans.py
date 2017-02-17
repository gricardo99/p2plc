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

import sys, getopt


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

def get_loan_list_file(file_name):
	return pd.read_pickle(file_name)

def get_loan_list():
	loanlist_url = get_url(0,'loans/listing');
	loan_list = session.get(loanlist_url, headers=headers)
	if (loan_list.status_code == 200):
		loans_j = loan_list.json()
		if 'loans' in loans_j:
			mydf = json_normalize(loan_list.json()['loans'])
			return mydf
		else:
			logging.debug("No loans listed!");
			logging.debug(loans_j);
			sys.exit ()
	else:
		logging.debug("get loan list returned status code:%d",loan_list.status_code)
		sys.exit ()


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

def add_orders(ords,portf_name,loans,max_buy):
	if (ords == ""):
		ords = parent_order()
	else:
		ords += ',\n'
        for p in config['portfolios']:
                if (p['portfolioName']==portf_name):
                        portf_id = p['portfolioId']
                        break
        for index, row in loans.iterrows():
                ords += gen_order(portf_id,row)
                if (index<len(loans)-1) and (index<max_buy-1):
                        ords += ',\n'
                if (index<max_buy):
                        break
	return ords

def send_orders(ords,ords_logfile):
        ords += '\t]\n'
        ords += '}'
	order_payload_name = "log/" + cur_date + "/orders.json"
	order_resp_name = "log/" + cur_date + "/resp.json"
	logging.debug("order_payload_name:%s",ords_logfile)
	logging.debug("order_resp_name:%s",order_resp_name)
	pyld_f = open(ords_logfile, 'w')
	resp_f = open(order_resp_name, 'w')
	logging.debug("created order and resp files.");
	order_url = get_url(1,'orders')
	logging.debug("order_url:%s",order_url)
	logging.debug("order payload:%s",ords)
	json.dump(ords,pyld_f)
	ordresp = session.post(order_url, headers=headers, data=ords)
	logging.debug("ordresp:%s",ordresp)
	json.dump(ordresp.json(),resp_f)
	return ordresp


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

try:
	opts, args = getopt.getopt(sys.argv[1:],"ts:",["test","datasrc="])
except getopt.GetoptError:
	print 'getloans.py <-t> '
	sys.exit(2)

testmode = False
datasrc = 'url'

for opt, arg in opts:
	if opt == '-t':
		testmode = True
	if opt == '-s':
		datasrc = arg

cur_date = time.strftime("%Y.%m.%d")
release_tm =  time.strftime("%I%p_%M:%S")
dirname = "data/pandas/" + cur_date
logname = "log/" + cur_date

if testmode:
	cur_data = ""
	realease_tm = ""
	dirname = "data/test"
	logname = "log/test"

order_payload_name = logname + "/orders.json"
if not os.path.exists(dirname):
    os.makedirs(dirname)
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

if datasrc == 'url':
	mydf = get_loan_list()
if datasrc == 'file':
	file_name = "data/pandas/2017.02.15/newlisted_02PM_00:01.pkl"
	mydf = get_loan_list_file(file_name)

if datasrc != 'file':
	newlisted_f = "newlisted_" + release_tm + ".pkl";
	mydf.to_pickle(dirname + '/' + newlisted_f) 
all_ords = ""

for pf in config['portfolios']:
	port_match = mydf.query(pf['query'])
	portmatch_f = dirname + "/" + pf['portfolioName'].lower() + "_" + release_tm + ".pkl";
	if not port_match.empty:
		if (not os.path.exists(order_payload_name)):
			port_match.sort(['intRate','dti'],ascending=[False,True],inplace=True)
			port_match.reset_index(drop=True, inplace=True)
			logging.debug("gen orders for port:%s",pf['portfolioName'])
			all_ords = add_orders(all_ords,pf['portfolioName'],port_match,1)
		else:
			logging.debug("skipping orders for portfolio:%s",pf['portfolioName']);
		port_match.to_pickle(portmatch_f) 
		logging.debug("written pickle to %s",portmatch_f)
	else:
		logging.debug("skipping orders, no matches for portfolio:%s",pf['portfolioName']);
		open(portmatch_f, 'a').close()

if (all_ords!=""):
	ord_resp = send_orders(all_ords,order_payload_name)
	logging.debug("order status_code:%s",ord_resp.status_code);
	if ord_resp.status_code == 200:
		logging.debug("order success");
		logging.debug(ord_resp.json());
	else:
		logging.debug("order failed!");
		logging.debug(ord_resp.json());

logging.debug("Exit. Done.");
