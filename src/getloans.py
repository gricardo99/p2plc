import pandas as pd
import numpy as np
import requests
import time
from pandas.io.json import json_normalize
import json
import os
import logging
import sys, getopt

# my modules
import config
import portfolios


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

config = config.load_config()
base_url = config['baseUrl']  + config['apiVer'];
acct_suffix_url = '/accounts/' + config['investorId'];
headers = {'Authorization': config['apiKey'], 'Accept': 'application/json', 'Content-Type': 'application/json', 'X-LC-LISTING-VERSION': '1.3'}

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
		json_err = loan_list.json()
		logging.debug("get loan list returned error json:%s",json_err)
		sys.exit ()

def parent_order():
        return { 'aid': config['investorId'], 'orders': []}

def gen_order(pf,loan):
        return { 'loanId' : loan[['id']].item(), 'requestedAmount': pf['orderAmount'], 'portfolioId' : pf['portfolioId']} 

def add_orders(ords,pf,loans):
	for index, row in loans.iterrows():
		ords['orders'].append(gen_order(pf,row))
		if (index>=pf['maxDayOrders']-1):
				break
	return ords

def send_orders(ords):
	order_url = get_url(1,'orders')
	logging.debug("order_url:%s",order_url)
	logging.debug("order payload:%s",ords)
	ordresp = session.post(order_url, headers=headers, data=json.dumps(ords))
	logging.debug("ordresp:%s",ordresp)
	return ordresp


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
	portfolios.save_path = dirname + "/"

order_payload_name = logname + "/orders.json"
order_resp_name = logname + "/resp.json"
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
lsum_cols = ['term','intRate','fundedAmount','loanAmount','installment','purpose','annualInc','dti','empLength']

if datasrc == 'url':
	mydf = get_loan_list()
if datasrc == 'file':
	file_name = "data/pandas/2017.02.22/newlisted_10AM_00:02.pkl"
	mydf = get_loan_list_file(file_name)

if datasrc != 'file':
	newlisted_f = "newlisted_" + release_tm + ".pkl";
	mydf.to_pickle(dirname + '/' + newlisted_f) 
all_ords = parent_order();

submitted_ords = { 'todayOrders' : []}
resp_ords = { 'todayOrderConfirmations': [] }
portfolios.load_portfolios()
portfolios.load_order_hist(order_payload_name,order_resp_name,submitted_ords,resp_ords)

for pn in portfolios.pfls.keys():
	pf = portfolios.pfls[pn]
	port_match = portfolios.filter_ll(pn,mydf)
	portmatch_f = dirname + "/" + pn.lower() + "_" + release_tm + ".pkl";
	if not port_match.empty:
		if pf['numOrders']:
			pf['loan_matches'] = port_match
			logging.debug("gen orders for port:%s",pn)
			add_orders(all_ords,pf,port_match)
		else:
			logging.debug("skipping orders. already filled:%d orders for portfolio:%s",pf['todayFilledOrdCount'],pn)
		port_match.to_pickle(portmatch_f) 
		logging.debug("written pickle to %s",portmatch_f)
	else:
		logging.debug("skipping orders, no matching loans for portfolio:%s",pn)
		open(portmatch_f, 'a').close()

if (all_ords['orders']):
	submitted_ords['todayOrders'].append(all_ords)
	pyld_f = open(order_payload_name, 'w')
	json.dump(submitted_ords,pyld_f)
	logging.debug("wrote order_payload_name:%s",order_payload_name)
	logging.debug("all ords today:")
	logging.debug(submitted_ords)
	ord_resp = send_orders(all_ords)
	logging.debug("order status_code:%s",ord_resp.status_code);
	if ord_resp.status_code == 200:
		logging.debug("order success")
		cur_ord_resp_j = ord_resp.json()
		logging.debug(cur_ord_resp_j)
		logging.debug("order_resp_name:%s",order_resp_name)
		resp_ords['todayOrderConfirmations'].append(cur_ord_resp_j)
		resp_f = open(order_resp_name, 'w')
		json.dump(resp_ords,resp_f)
		portfolios.update_ids(all_ords['orders'],cur_ord_resp_j['orderConfirmations'])
	else:
		logging.debug("order failed!");
		try:
			logging.debug(ord_resp.json());
		except:
			logging.debug("cannot decode json response")


logging.debug("Exit. Done.");
