#!/usr/bin/env python
# filename = utils.py

import sys
import json
import csv
from urlparse import urlparse

def clean_urls(dirty_url):
	""" Strip protocol and trailing '/' from blog info profided by GitHub profile"""
	url = urlparse(dirty_url)
	if url.path == '/':
		clean_url = url.netloc
	else:
		clean_url = url.netloc + url.path
	return clean_url


def normalize(s):
	# add line to remove accents later using: unicodedata.normalize('NFKD', string)
	if s:
		s = s.lower()
		return s
	else:
		return



def setup():
	"""
	Parses the arguments and returns a list of dictionaries. Each dictionary
	contains name, location, company and website of a person to look up.
	""" 
	NAME = 0
	CITY = 1
	COMPANY = 2
	BLOG = 3
	GIT_USERNAME = 4
	EMAIL =5
	gh_profiles = []
	
	if len(sys.argv) > 1 and sys.argv[1] == "-f":
		# load profiles from a CSV file
		with open(sys.argv[2], 'r') as csvfile:
			f = csv.reader(csvfile)
			for row in f:
				git_url = "github.com/" + row[GIT_USERNAME]
				gh_profiles.append({'name': row[NAME],
					'city': normalize(row[CITY]),
					'company': row[COMPANY],
					'website': clean_urls(row[BLOG]),
					'github_url': git_url,
					'email': row[EMAIL]
				})
	elif len(sys.argv) > 1 and sys.argv[1] == "-n":
		# we are looking up a single individual. Details entered at the command line
		pass 
	else:
		print('Usage:\n $ profilefinder.py -f filename #file must be in CSV format.\n $ profilefinder.py -n [name="first last" location="city" company="company name", blog="url"]')
	
	# specify the log file
	filename = sys.argv[2][:sys.argv[2].rfind('.')]
	logfile = filename + ".log"
	
	return gh_profiles, logfile


def save_as_json(data_struc, filename):
	""" converts the data structure to a json string and writes it to file """
	data_string = ""
	fname = 'Data/' + filename + '.json'
	data_string = json.dumps(data_struc)
	with open(fname, 'w') as f:
		f.write(data_string)
	return


def load_json(filename):
	""" loads a json file from disk and converts back to original data structure """
	data_string = ""
	fname = 'Data/' + filename + '.json'
	with open(fname, 'r') as f:
		data_string = f.read()
	data_struc = json.loads(data_string)
	return data_struc


def print_results(devs):	
	print
	for dev in devs:
		if dev['li_matches']:
			if dev['li_matches'][0]['score'] >= 75:
				msg = "YES (%d): %s" % (dev['li_matches'][0]['score'] ,dev.get('name'))
				#f.writelines(msg + '\n')
				print msg
			elif dev['li_matches'][0]['score'] >= 0:
				msg = "MAYBE (%d): %s" % (dev['li_matches'][0]['score'] ,dev.get('name'))
				#f.writelines(msg + '\n')
				print msg
			else:
				msg = "NO (%d): %s" % (dev['li_matches'][0]['score'] ,dev.get('name'))
				#f.writelines(msg + '\n')
				print msg
		else:
			msg = "NO (n/a): %s" % dev.get('name')
			#f.writelines(msg + '\n')
			print msg
	return


def check_li_parsing_and_matching(devs):	
	for dev in devs:
		print "\nName:", dev['name']
		print "Company:", dev['company']
		print "Website:", dev['website']
		print "Email:", dev['email']
		for match in dev['li_matches']:
			if match['parsed_profile']:
				print "Found LinkedIn websites:", match['parsed_profile']['websites']
				print "Found LinkedIn employment:", match['parsed_profile']['employment']
	return


def sanity_check(devs):
	with open('Data/sanity_check.csv', 'w') as f:
		print
		for dev in devs:
			if dev['li_matches']:
				if dev['li_matches'][0]['score'] >= 75:
					msg = "YES, %d, %s, %s, %s" % (dev['li_matches'][0]['score'], dev.get('name'), dev['github_url'], dev['li_matches'][0]['url'])
					f.writelines(msg + '\n')
					print msg
				elif dev['li_matches'][0]['score'] >= 0:
					msg = "MAYBE, %d, %s, %s, %s" % (dev['li_matches'][0]['score'], dev.get('name'), dev['github_url'], dev['li_matches'][0]['url'])
					f.writelines(msg + '\n')
					print msg
				else:
					msg = "NO, %d, %s, %s, " % (dev['li_matches'][0]['score'] ,dev.get('name'), dev['github_url'])
					f.writelines(msg + '\n')
					print msg
			else:
				msg = "NO (n/a): %s" % dev.get('name')
				f.writelines(msg + '\n')
				print msg
	return


