import netrc

default_netrc_host = 'api.lendingclub.com'

def load_netrc(host=default_netrc_host):
	info = netrc.netrc()
	return info.authenticators(host)

def load_account():
	return load_netrc()

