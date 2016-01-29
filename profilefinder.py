#!/usr/bin/env python

import sys



def setup():
	"""
	Parses the arguments and returns a list of dictionaries. Each dictionary
	contains name, location, company and website of a person to look up.
	"""	
	NAME = 0
	CITY = 1
	COMPANY = 2
	BLOG = 3
	names = []
	
	if len(sys.argv) > 1 and sys.argv[1] == "-f":
		# we are reading from a CSV file
		with open(sys.argv[2], 'r') as f:
			lines = f.readlines()
			for line in lines:
				lst = line.strip().replace('"','').split(',')
				names.append({'name': unicode(lst[NAME], 'utf-8'), 'city': unicode(lst[CITY], 'utf-8'),
				'company': unicode(lst[COMPANY], 'utf-8'), 'blog': unicode(lst[BLOG], 'utf-8')})
	elif len(sys.argv) > 1 and sys.argv[1] == "-n":
		# we are looking up a single individual. Details entered at the command line
		pass 
	else:
		print('Usage:\n $ profilefinder.py -f filename #file must be in CSV format.\n $ profilefinder.py -n [name="first last" location="city" company="company name", blog="url"]')
	
	return names


def googlename():
	"""
	Googles a name to find promising LinkedIn profiles. For exact name matches
	from the first page of results, returns the LinkedIn public profile urls in
	a list.
	"""
	pass
	return


def scoreprofile():
	"""
	Parsed the LinkedIn public profiles, scores them and returns a list,
	sorted by highest score, of the urls that might be matches.
	"""
	return 


if __name__ == '__main__':
	
	lst = setup()
	print "number of people to look up:", len(lst)
	print lst[0].get('name'), lst[0].get('city'), lst[0].get('company'), lst[0].get('blog')
	print lst[1].get('name'), lst[1].get('city'), lst[1].get('company'), lst[1].get('blog')
	print lst[2].get('name'), lst[2].get('city'), lst[2].get('company'), lst[2].get('blog')