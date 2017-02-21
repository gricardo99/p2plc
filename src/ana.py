import pandas as pd
import numpy as np
import requests as req
import json
import os
import glob
import time
import netrc

import config 

from pandas.io.json import json_normalize


def create_portf(name,desc):
	url = get_url(1,'portfolios')
	print url
	payload = {'actorId': config['investorId'], 'portfolioName': name, 'portfolioDescription': desc}
	print payload
	r = req.post(url, headers=myheaders, data=json.dumps(payload))
	return r 


file_name = "data/pandas/2017.01.30/newmatch_10AM_01:02.pkl"
file_name = "data/pandas/2017.02.04/newmatch_06AM_01:02.pkl"
file_name = "data/pandas/2017.02.20/newlisted_06AM_00:02.pkl"
file_name = "data/pandas/2017.02.17/newlisted_02PM_00:01.pkl"

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


