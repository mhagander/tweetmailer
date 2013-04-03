#!/usr/bin/env python

import sys
import time
import urllib
import re
import ConfigParser
from subprocess import Popen, PIPE

import simplejson as json

from email.mime.text import MIMEText

def sendmail(msg):
	pipe = Popen("/usr/sbin/sendmail -t", shell=True, stdin=PIPE).stdin
	pipe.write(msg.as_string())
	pipe.close()

if __name__=="__main__":
	cfg = ConfigParser.ConfigParser()
	cfg.read('tweetmailer.ini')

	try:
		twitteruser = cfg.get('twitter', 'user')
	except:
		print "Need option 'user' in section 'twitter' in tweetmailer.ini"
		sys.exit(1)

	try:
		email_to = cfg.get('email', 'to')
		email_from = cfg.get('email', 'from')
	except:
		print "Need options 'to' and 'from' in section 'email' in tweetmailer.ini"
		sys.exit(1)


	try:
		lasttweet = int(cfg.get('twitter', 'lasttweet'))
	except:
		# It's ok not to have a lasttweet if this is the first run
		lasttweet = 0
		pass

	params = {
		"screen_name" : twitteruser,
		"trim_user" : 1,
		"include_entities": 0,
		}
	if lasttweet:
		params['since_id'] = lasttweet

	u = urllib.urlopen("http://api.twitter.com/1/statuses/user_timeline.json?%s" % urllib.urlencode(params))
	result = u.read()
	try:
		d = json.loads(result)
	except:
		if re.search("Twitter is currently down for maintenance.", result):
			sys.exit(0)

		print "Unable to parse json: %s" % result
		sys.exit(1)

	if len(d):
		first = True
		newmax = lasttweet
		for t in sorted(d, key=lambda k: k['id']):
			if not first:
				# Sleep if there is more than one email to send, just so we
				# don't get rate limited or something
				time.sleep(10)
			else:
				first = False

			msg = MIMEText('', _charset='utf-8')
			msg['Subject'] = t['text']
			msg['To'] = email_to
			msg['From'] = email_from
			sendmail(msg)
			print "Sent '%s'" % t['text']

			if t['id'] > newmax:
				newmax = t['id']

		cfg.set('twitter', 'lasttweet', newmax)
		with open('tweetmailer.ini', 'w') as f:
			cfg.write(f)

