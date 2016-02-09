#!/usr/bin/env python
# filename = utils.py

import pickle
import json

def pickle_data(data, filename):
	fname = filename + '.pkl'
	with open(fname, 'wb') as f:
		pickle.dump(data, f)
	return


def unpickle_data(filename):
	fname = filename + '.pkl'
	with open(fname, 'rb') as f:
		data = pickle.load(f)
	return data


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


