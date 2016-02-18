#!/usr/bin/env python

import csv
import sys
import re
import urllib
from urlparse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import liparser
import piplsearch
import utils
import pdb

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


def google_for_li_matches(person):
	"""
	Googles a name to find promising LinkedIn profiles. For exact name matches
	from the first page of results, returns the LinkedIn public profile urls in
	a list.
	"""
	gh_name = person.get('name')
	gh_city = person.get('city')
	li_profiles = []
	
	# perform the Google search
	dcap = dict(DesiredCapabilities.PHANTOMJS)
	dcap['phantomjs.page.settings.userAgent'] = ("Mozilla/5.0 (X11; Linux x86_64) \
					AppleWebKit/53 " "(KHTML, like Gecko) Chrome/15.0.87")
	driver = webdriver.PhantomJS(desired_capabilities=dcap)
	driver.get('http://www.google.com')
	input_box = driver.find_element_by_name("q")
	input_box.send_keys(gh_name + " " + gh_city + " software" + " site:linkedin.com")
	input_box.submit()
	try:
		WebDriverWait(driver, 5).until(EC.title_contains(gh_name))
		page = driver.page_source
	except:
		print "Timeout googleing for %s." % gh_name
		return
	finally:
		driver.quit()
		
	# parse the search results
	url_pattern = re.compile(r'q=(h.+?)&')
	soup = BeautifulSoup(page, "html5lib")
	results = soup.select('h3.r')
	for result in results:
		# test each results for an exact name match
		li_name = result.a.get_text()
		li_name_cleaned = li_name[:li_name.find('|')].strip()
		if normalize(li_name_cleaned) == normalize(gh_name):
			# get the link to this LinkedIn profile
			match = re.search(url_pattern, result.a['href'])
			if match:
				match_url = {'url': match.group(1), 'score':'', 'parsed_profile':''}
				li_profiles.append(match_url)
				
	return li_profiles


def evaluate_li_matches(person):
	"""
	Receives a list of linkedIn profile URLs that might belong to "person".
	Tries to load, parse and score each potential match. Returns the sorted 
	list (best match first).
	"""
	for match in person['li_matches']:
		# fetch and parse the LinkedIn profile
		parsed_profile = liparser.parse_li_profile(match.get('url'), person.get('name'))
		
		# if we are able to parse the profile, then score it
		if parsed_profile:	#.get('name'):
			match['score'] = score_li_matches(person, parsed_profile)
			match['parsed_profile'] = parsed_profile
		else:
			match['score'] = -1	# unable to parse the LinkedIn page
	
	# sort from highest scoring match to lowest
	return sorted(person['li_matches'], key =lambda k: k['score'], reverse=True)


def score_li_matches(gh, li):
	"""
	Receives a GitHub developer's profile (gh) and a parsed LinkedIn 
	profile (li). Tries to find information in the li that matches 
	that of the gh. Scores according to how many common items they have.
	"""
	def test_location():
		score = 0
		if gh.get('city') in li.get('location'): 
			score = 25
		return score
	
	def test_employment():
		score = 0
		job = ''
		jobs = []
		
		if gh.get('company'):
			# get company listed in the GitHub profile
			job  = normalize(gh.get('company'))
		
			# match GitHub company against LinkedIn employment history.
			if li.get('employment'):
				jobs = map(normalize, [position['company name'] for position in li['employment']])
				if job in jobs:
					score += 50
		
			# match GitHub company against employer in the Linkedin profile Headline. 
			if li.get('headline'):
				if li['headline']['employer']:
					jobs = normalize(li['headline']['employer'])
					if job in jobs:
						score += 50
					
		# elif
			# TODO: match email and personal website domain against LinkedIn employment history.
		else:
			# we have nothing in GitHub we can use to match agaist LinkedIn employment history.
			pass
			
		return score
	
	def test_websites():
		score = 0
		
		# blog listed on GitHub user profile page
		web = set([gh.get('website')])
		
		# we add the GitHub user's profile page
		web.add(gh.get('github_url'))
		
		# websites listed on the Linkedin profile we are scoring
		webs = set(li.get('websites').values())
		
		# compare the two sets
		if web & webs:
			score = 100 * len(web & webs)
		return score
	
	
	return sum([test_location(), test_employment(), test_websites()])


def try_piplsearch(person):
	dic = {}
	results = piplsearch.pipl_search({'email': person.get('email')})
	# if found some LinkedIN profiles, convert to std form
	for socmedia in [socmedia for socmedia in results if socmedia['site_name']=='LinkedIn']:
		parsed_profile = parse_a_li_profile(socmedia.get('url'), dev.get('name'))
		dic = {'url': socmedia.get('url'), 'score': 99, 'parsed_profile': parsed_profile}
		dev['li_matches'].append(dic)
	return dic



if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf-8')
	devs, log = utils.setup()
	
	
	# Use Google to find potential LinkedIn matches
	for dev in devs:
		try:
			print'\rGoogling for matches for %s...' % dev.get('name')
			dev['li_matches'] = google_for_li_matches(dev)
		except:
			print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,dev['name'])
			continue
	utils.save_as_json(devs, 'googlesearchresults')
	print "Done.\n"
	
	
	# Compare the LinkedIn profiles to the GitHub profile, score them and sort them. Return best at index[0]
	devs = utils.load_json('googlesearchresults')
	for dev in devs:
		print '\rEvaluating matches for %s...' % dev.get('name')
		dev['li_matches'] = evaluate_li_matches(dev)
	utils.save_as_json(devs, 'scoredresults')
	print "Done.\n"
	
				
	"""
	# Use Pipl to match remainder
	for dev in [dev for dev in devs if dev['email']]:
		if dev['li_matches']:
			if dev['li_matches'][0]['score'] < 75:
				print "Trying piplsearch for %s..." % dev.get('name')
				result = try_piplsearch(dev)
				if result:
					dev['li_matches'].append(result)
					# re-sort from highest scoring match to lowest
					dev['li_matches'] = sorted(dev['li_matches'], key =lambda k: k['score'], reverse=True)
		else:
			print "Trying piplsearch for %s..." % dev.get('name')
			result = try_piplsearch(dev)
			if result:
				dev['li_matches'].append(result)
				# re-sort from highest scoring match to lowest
				dev['li_matches'] = sorted(dev['li_matches'], key =lambda k: k['score'], reverse=True)
	"""
		
		
	# See the results of running through both algos
	#devs = utils.load_json('scoredresults')
	utils.print_results(devs)
	
	#utils.sanity_check(devs)
	

