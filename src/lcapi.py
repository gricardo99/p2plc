import pandas as pd
import numpy as np
import requests
import time
from pandas.io.json import json_normalize
import json
import os
import logging

class lcApi:
	def __init__(self, investorId, apiKey, base_url='https://api.lendingclub.com/api/investor/', ver='v1'):
		self.base_url = config['baseUrl']  + ver
		self.acct_suffix_url = '/accounts/' + investorId
		self.headers = {'Authorization': apiKey, 'Accept': 'application/json', 'Content-Type': 'application/json', 'X-LC-LISTING-VERSION': '1.1'}
		self.session = requests.Session()
		self.session.trust_env = False

	def get_url(self,acct,action):
			if (acct) :
					suf = self.acct_suffix_url
			else :
					suf = ''
			return self.base_url + suf + "/" + action;

	def get_loan_list_file(file_name):
		return pd.read_pickle(file_name)

	def get_loan_list(self):
		loanlist_url = self.get_url(0,'loans/listing');
		loan_list = self.session.get(loanlist_url, headers=self.headers)
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

	def parent_order(self):
			return { 'aid': config['investorId'], 'orders': []}

	def gen_order(self,pf,loan):
			return { 'loanId' : loan[['id']].item(), 'requestedAmount': pf['orderAmount'], 'portfolioId' : pf['portfolioId']} 

	def add_orders(ords,pf,loans):
		for index, row in loans.iterrows():
			ords['orders'].append(gen_order(pf,row))
			if (index>=pf['maxDayOrders']-1):
					break
		return ords

	def send_orders(self,ords,resp_logfile,ords_logfile):
		logging.debug("order_payload_name:%s",ords_logfile)
		pyld_f = open(ords_logfile, 'w')
		logging.debug("created order file.");
		order_url = get_url(1,'orders')
		logging.debug("order_url:%s",order_url)
		logging.debug("order payload:%s",ords)
		json.dump(ords,pyld_f)
		ordresp = self.session.post(order_url, headers=self.headers, data=json.dumps(ords))
		logging.debug("ordresp:%s",ordresp)
		if (ordresp.status_code == 200):
			logging.debug("order_resp_name:%s",resp_logfile)
			resp_f = open(resp_logfile, 'w')
			json.dump(ordresp.json(),resp_f)
		return ordresp

	def get_summary(self)
		sum_url = get_url(1,'summary');
		r = session.get(sum_url, headers=self.headers)
		return r



