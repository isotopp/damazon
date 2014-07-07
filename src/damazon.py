#!/usr/bin/python

# setup: pip install requests beautifulsoup4

from decimal import Decimal
import requests
from bs4 import BeautifulSoup
import sys
import getpass

host = raw_input("Amazon Host: (default: www.amazon.de) ")
if not host:
   host = 'www.amazon.de'    
if host.endswith('.com'):
   currency = 'USD'
elif host.endswith('.co.uk'):
   currency = 'GBP'
else:
   currency = 'EUR'

username = raw_input("Username: ")
password = getpass.getpass("Password: ")
# Session setup
session = requests.Session()
session.headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.3 Safari/537.36"

# Request login page
login_r = session.get("https://%s/gp/css/order-history/" % (host))
login = BeautifulSoup(login_r.content)

payload = {'email': username, 'password': password}
for x in login.find_all("input", type="hidden"):
	payload[x.attrs['name']] = x.attrs['value']

# Log in
order_r = session.post("https://%s/ap/signin" % (host), data=payload, allow_redirects=False)

# Request order history
hist_r = session.get("https://%s/gp/css/order-history/" % (host))

soup = BeautifulSoup(hist_r.content)
filters = [options.attrs['value'] for options in soup.find('select', id='orderFilter').findChildren()[1:]]

print "[+] Found %d filters, processing..." % len(filters)

total = Decimal("0.00")
total_orders = 0

for scope in filters:
	scope_r = session.get("https://%s/gp/css/order-history/?ie=UTF8&orderFilter=%s&startIndex=0" % (host, scope))
	scope_soup = BeautifulSoup(scope_r.content)
	try:
		length = int(scope_soup.find('div', 'num-results').b.text)
	except AttributeError:
		length = 0
	sys.stdout.write("[+] Processing %s \t(%s orders)... " % (scope.rjust(9), str(length).rjust(4)))
	sys.stdout.flush()
	page = 10
	scope_sum = Decimal("0.00")
	for x in scope_soup.find_all('span', 'price'):
		if host.endswith('.com') or host.endswith('.co.uk'):
			scope_sum += Decimal(x.text[1:])
		else:
			scope_sum += Decimal(x.text[4:].replace(".","").replace(",","."))
		scope_sum += Decimal(x.text[4:].replace(",","."))
	while page <= length:
		scope_page_r = session.get("https://%s/gp/css/order-history/?ie=UTF8&orderFilter=%s&startIndex=%d" % (host, scope, page))
		for y in BeautifulSoup(scope_page_r.content).find_all('span', 'price'):
			if host.endswith('.com'):
				scope_sum += Decimal(x.text[1:])
			else:
				scope_sum += Decimal(y.text[4:].replace(".","").replace(",","."))
		page += 10
	print "\t%s %s" % (str(scope_sum).rjust(10), currency)
	if scope.startswith("year"):
		total += scope_sum
		total_orders += length

print "[+] Grand total (years only) \t(%s orders)... \t%s %s" % (str(total_orders).rjust(4), str(total).rjust(10), currency)
