import pandas as pd
import numpy as np
import requests as req
import json
import os
import time
from pandas.io.json import json_normalize

with open('config/config.json', 'r') as f:
    config = json.load(f)

base_url = config['baseUrl']  + config['apiVer'];
acct_suffix_url = '/accounts/' + config['investorId'];
headers = {'Authorization': config['apiKey']}

def get_url( acct,action ):
	if (acct) :
		suf = acct_suffix_url
	else :
		suf = ''
	return base_url + suf + "/" + action;


dirname = "data/pandas/" + time.strftime("%Y.%m.%d")
release_tm = time.strftime("%I%p_%M:%S");
if not os.path.exists(dirname):
    os.makedirs(dirname)

loanlist_url = get_url(0,'loans/listing');
loan_list = req.get(loanlist_url, headers=headers);
mydf = json_normalize(loan_list.json()['loans'])

lsum_cols = ['term','intRate','fundedAmount','loanAmount','installment','purpose','annualInc','dti','empLength']

resdf = mydf.query('(term<=36) and ((grade == "B") or (grade == "C")) and (annualInc>=70000) and (dti<=20) and (empLength>=24) and (installment<=500) and (pubRec==0) and (not (mthsSinceLastDelinq > 0))');

newlisted_f = "newlisted_" + release_tm + ".pkl";
newmatch_f = "newmatch_" + release_tm + ".pkl";

mydf.to_pickle(dirname + '/' + newlisted_f) 
resdf.to_pickle(dirname + '/' + newmatch_f) 

