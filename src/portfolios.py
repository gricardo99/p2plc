import json
import os
import glob
import logging

default_portfolio_cfg_path = "config/portfolio/"
save_path = "data/state/"
loan_ids_f = "loan_ids.json"
member_ids_f = "member_ids.json"

all_loan_ids = []
all_member_ids = []
pfls = {}

def load_id_file(id_f):
	if (os.path.exists(id_f)):
		with open(id_f, 'r') as f:
			return json.load(f)
	return []

def save_id_file(id_f,new_l):
	cur_list = load_id_file(id_f)
	if len(new_l)<=len(cur_list):
		logging.debug("This is an error. length of new list should be longer.  File:%s",id_f) 
		return
	with open(id_f, 'w') as f:
		json.dump(new_l,f)

def load_portfolios(loan_file=loan_ids_f,mem_file=member_ids_f,config_path=default_portfolio_cfg_path):
	for fn in glob.glob(config_path + "*.json"):
		port_name = (os.path.splitext(os.path.basename(fn))[0]).upper()
		with open(fn, 'r') as f:
			cur_port = json.load(f)
			pfls[port_name] = cur_port
	loan_ids_f = save_path + loan_file
	all_loan_ids = load_id_file(loan_ids_f)
	member_ids_f = save_path + mem_file
	all_member_ids = load_id_file(member_ids_f)
	return pfls


def load_order_hist(order_payload_name,order_resp_name):
	submitted_ords = { 'orders' : []}
	resp_ords = { 'orderConfirmations': [] }
	if (os.path.exists(order_payload_name)):
		with open(order_payload_name, 'r') as f:
			submitted_ords = json.load(f)
		if (not os.path.exists(order_resp_name)):
			logging.debug("This is a problem.  Why doesnt this exist:%s",order_resp_name)
		else:
			with open(order_resp_name, 'r') as f:
				resp_ords = json.load(f)
	set_allowed_cnt(submitted_ords['orders'],resp_ords['orderConfirmations'])



def set_allowed_cnt(sent_ords,ord_confs):
	skip_orders = False
	for ords in sent_ords:
		orsp = filter(lambda loanid: loanid['loanId'] == ords['loanId'],ord_confs)
		if not orsp:
			logging.debug("This is also a problem.  Why dont we have a response for this order:%s",ords)
			logging.debug("responses:%s",ord_confs)
			skip_orders = True
		else:
			orsp = orsp[0]
			logging.debug("previous response for order:%s",orsp)
			portf_match = filter(lambda cur_port: cur_port['portfolioId'] == ords['portfolioId'],pfls.values())
			if not portf_match:
				logging.debug("This is, wtf, a problem.  Why dont we have a portfolio for this order:%s",ords)
				skip_orders = True
			else:
				portf_match = portf_match[0]
				pf = pfls[portf_match['portfolioName']]
				pf['todayFilledOrdCount'] = pf.get('todayFilledOrdCount',0)
				if 'ORDER_FULFILLED' in orsp['executionStatus']:
					pf['todayFilledOrdCount'] = pf.get('todayFilledOrdCount',0) + 1
				else:
					logging.debug("This order was not filled.  Order:%s",ords)
					logging.debug("Response:%s",orsp)
	for pf in pfls.values():
		pf['todayFilledOrdCount'] = pf.get('todayFilledOrdCount',0)
		if skip_orders:
			pf['numOrders'] = 0
		else:
			pf['numOrders'] = pf['maxDayOrders'] - pf['todayFilledOrdCount']

def filter_ll(pn,df):
	port_match = df.query(pfls[pn]['query'])
	port_match = port_match.loc[~port_match['id'].isin(all_loan_ids)]
	port_match = port_match.loc[~port_match['memberId'].isin(all_member_ids)]
	port_match.sort(['intRate','dti'],ascending=[False,True],inplace=True)
	port_match.reset_index(drop=True, inplace=True)
	return port_match

def update_ids(sent_ords,ord_confs):
	for ords in sent_ords:
		orsp = filter(lambda loanid: loanid['loanId'] == ords['loanId'],ord_confs)
		if not orsp:
			logging.debug("update_state: This is also a problem.  Why dont we have a response for this order:%s",ords)
			logging.debug("responses:%s",ord_confs)
		else:
			orsp = orsp[0]
			if 'ORDER_FULFILLED' in orsp['executionStatus']:
				all_loan_ids.append(orsp['loanId'])
				portf_match = filter(lambda cur_port: cur_port['portfolioId'] == ords['portfolioId'],pfls.values())
				if not portf_match:
					logging.debug("update_state: This is, wtf, a problem.  Why dont we have a portfolio for this order:%s",ords)
				else:
					portf_match = portf_match[0]
					pdf = pfls[portf_match['portfolioName']]['loan_matches']
					loan_list = pdf.loc[pdf['id'] == orsp['loanId']]
					if len(loan_list.index)==1:
						all_member_ids.append(loan_list['memberId'].item())
					else:
						logging.debug("update_state: why not one row for loan? loan_matches:")
						logging.debug(pdf)
	save_id_file(loan_ids_f,all_loan_ids)
	save_id_file(member_ids_f,all_member_ids)


