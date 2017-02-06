import pandas as pd
import numpy as np
import requests as req
import json
import os
import glob
import time
import netrc

from pandas.io.json import json_normalize

with open('config/config.json', 'r') as f:
    config = json.load(f)

base_url = config['baseUrl']  + config['apiVer'];
info = netrc.netrc()
config['investorId'], account, config['apiKey'] = info.authenticators("api.lendingclub.com")
acct_suffix_url = '/accounts/' + config['investorId'];
myheaders = {'Authorization': config['apiKey'], 'content-type': 'application/json'}
maxorders = 1

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


def all_orders(portf_name,loans):
	po = parent_order()
	num_orders = 0
	for p in config['portfolios']:
 		if (p['portfolioName']==portf_name):
			portf_id = p['portfolioId']
			break
	done = False
	for index, row in loans.iterrows():
		po += gen_order(portf_id,row)
		num_orders += 1
		if (num_orders>=maxorders):
			done = True
		if (index<len(loans)-1) and not done:
			po += ',\n'
		else:
			po += '\n'
		if (done):
			break
	po += '\t]\n'
	po += '}'
	return po

def create_portf(name,desc):
	url = get_url(1,'portfolios')
	print url
	payload = {'actorId': config['investorId'], 'portfolioName': name, 'portfolioDescription': desc}
	print payload
	r = req.post(url, headers=myheaders, data=json.dumps(payload))
	return r 


file_name = "data/pandas/2017.01.30/newmatch_10AM_01:02.pkl"
file_name = "data/pandas/2017.02.04/newmatch_06AM_01:02.pkl"
file_name = "data/pandas/2017.01.30/newlisted_02PM_00:02.pkl"

lsum_cols = ['term','intRate','fundedAmount','loanAmount','installment','purpose','annualInc','dti','empLength']
appended_data = []
rdpath = 'data/pandas/'
for ddir in os.listdir(rdpath):
	dpath = rdpath + ddir	
	for filename in os.listdir(dpath):
		if filename.endswith(".pkl") and (("newmatch") in filename): 
			df_file = os.path.join(dpath, filename)
			print df_file
			cur_df = pd.read_pickle(df_file)
			if not cur_df.empty:
				print cur_df
				appended_data.append(cur_df)

df = pd.concat(appended_data) 
df.drop_duplicates(['id'], take_last=True,inplace=True)
df.sort_values(['intRate','installment'],ascending=[False,False],inplace=True)
df.reset_index(drop=True, inplace=True)
order_url = get_url(1,'orders')
print "order_url:" + order_url
payload = all_orders('HN1',df)

print payload
#r = req.post(order_url, headers=myheaders,data=payload)

#hn1_desc = "https://news.ycombinator.com/item?id=12320256"

#portf_url = get_url(1,'portfolios')
#print "portf URL:" + portf_url
#my_portf = req.get(portf_url, headers=myheaders)

#cp_res = create_portf('HN1',hn1_desc)
#print cp_res
#print cp_res.json()

#payload = {'actorId': config['investorId'], 'portfolioName': 'HN1', 'portfolioDescription': "my desc"}
#print payload
#r = req.post(portf_url, headers=myheaders, data=json.dumps(payload))

with open('data/test/order_resp.json') as data_file:    
    resp_ord = json.load(data_file)

conf_df = json_normalize(resp_ord['orderConfirmations'])
conf_len = len(conf_df['executionStatus'])
conf_df['orderInstructId'] = pd.Series(resp_ord['orderInstructId']*conf_len, index=conf_df.index)


