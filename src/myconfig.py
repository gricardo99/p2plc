import pandas as pd
import numpy as np
import requests as req
import json
from pandas.io.json import json_normalize

config = {'apiVer' : 'v1', 'baseUrl' : 'https://api.lendingclub.com/api/investor/' }

with open('config.json', 'w') as f:
    json.dump(config, f)

import pandas as pd
import numpy as np
import requests as req
import json
from pandas.io.json import json_normalize

with open('config/config.json', 'r') as f:
    config = json.load(f)

config['key3'] = 'value3'

base_url = config['baseUrl']  + '/' + config['apiKey'];
acct_suffix_url = '/accounts/' + config['investorId'];
headers = {'Authorization': apikey}

def get_url( acct,action ):
	if (acct) :
		suf = acct_suffix_url
	else :
		suf = ''
	return base_url + suf + "/" + action;

loanlist_url = get_url(0,'loans/listing');
loan_list = req.get(loanlist_url, headers=headers);
mydf = json_normalize(loan_list.json()['loans'])

lsum_cols = ['term','intRate','fundedAmount','loanAmount','installment','purpose','annualInc','dti','empLength']




