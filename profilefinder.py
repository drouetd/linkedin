#!/usr/bin/env python

import csv
import sys
import re
import urllib
from urlparse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import piplsearch
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


def get_matching_li_profiles(person):
	"""
	Googles a name to find promising LinkedIn profiles. For exact name matches
	from the first page of results, returns the LinkedIn public profile urls in
	a list.
	"""
	gh_name = person.get('name')
	gh_city = person.get('city')
	li_profiles = []
	
	# perform the Google search
	driver = webdriver.PhantomJS()
	driver.get('http://www.google.com')
	input_box = driver.find_element_by_name("q")
	#pdb.set_trace()
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
	#if len(li_profiles) == 0:
		#print "NO EXACT MATCHES FOUND FOR %s." % gh_name
	return li_profiles


def parse_a_li_profile(pub_url, fullname):
	"""
	Parses a LinkedIn profile page and returns the fields as structured data.
	"""
	def get_li_public_page(pub_url, fullname):
		page = ""
		driver = webdriver.PhantomJS()
		driver.get(pub_url)
		try:
			WebDriverWait(driver, 5).until(EC.title_contains(fullname))
			page = driver.page_source
		except:
			#print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,fullname)
			return
		finally:
			driver.quit()
		return page
	
	def get_headline():
		if soup.find("div", class_="profile-overview").find("p", class_="headline title"):
			s = soup.find("div", class_="profile-overview").find("p", class_="headline title").string
			at = s.find('at')
			profile['headline']['full'] = s.strip()
			profile['headline']['title'] = s[:at].strip()
			profile['headline']['employer'] = s[at + 2:].strip()
			
			# add the employer to profile['employment'] because people sometimes only update their headline.
			profile['employment'].append(profile['headline']['employer'])
		return
	
	def get_canonical_url():
		if soup.find("link", rel="canonical"):
			profile['canonical_url'] = soup.find("link", rel="canonical")['href']
		return
		
	
	def get_name():
		if soup.find("h1", id="name"):
			profile['name'] = soup.find("h1", id="name").string
		return
	
	def get_location():
		loc = soup.find("div", class_="profile-overview").find("span", class_="locality").string
		profile['location'] = normalize(loc)
		return
	
	def get_websites():
		company_num = 1    # handle multiple company websites
		table = soup.find("div", class_="profile-overview").find("table", class_="extra-info")
		if table.find("tr", class_="websites"):
			websites = table.find("tr", class_="websites").find_all("a")
			for site in websites:
				# key: handle multiple company websites being listed
				if site.string == "Company Website":
					key = "Company Website" + str(company_num)
					company_num += 1
				else:
					key = site.string 
				# value: strip the redirect and tracking info from urls
				url = urllib.unquote(str(site))
				start = url.find('?url=') + 5
				stop = url.rfind('&amp;urlhash')
				profile['websites'][key] = clean_urls(url[start:stop])
		return
	
	def get_employment():
		jobs = soup.find_all("li", class_="position")
		for job in jobs:
			company_name = job.find("h5", class_="item-subtitle", recursive=True).string
			profile['employment'].append(company_name)
		return
	
	
	# parsed LinkedIn profile will be returned as a dict
	profile = { 'canonical_url': '', 'name': '', 'headline': {},'location': {}, 'photo': '','employment': [],
				'education': [], 'websites': {}, 'skills':[]}
	
	# parse the LinkedIn profile
	page = get_li_public_page(pub_url, fullname)
	if page:
		soup = BeautifulSoup(page, 'html5lib')
		get_canonical_url()
		get_name()
		get_headline()
		get_location()
		# get_photo()
		get_employment()
		# get_education()
		get_websites()
		# get_skills()
	return profile


def evaluate_li_matches(person):
	""" score each potential match """
	for match in person['li_matches']:
		potential_match = parse_a_li_profile(match.get('url'), person.get('name'))
		if potential_match.get('name'):
			match['score'] = validate_url(person, potential_match)
			match['parsed_profile'] = potential_match
		else:
			match['score'] = -1	# unable to parse the LinkedIn page
	
	# sort from highest scoring match to lowest
	person['li_matches'] = sorted(person['li_matches'], key =lambda k: k['score'], reverse=True)
	return dev['li_matches']


def validate_url(person, data):
	def test_location():
		score = 0
		github_location = person.get('city')
		li_location = data.get('location')
		if github_location in li_location:
			#print "Matched location: ", github_location 
			score = 25
		return score
	
	def test_employment():
		score = 0
		job = set(map(normalize,[person.get('company')]))
		job.discard(None)	# to avoid a match if both the GiHub and LinkedIn profiles have no employer listed.
		#print "GitHub profile employer:", job
		jobs = set(map(normalize,data.get('employment')))
		#print "LinkedIn profile employers:", jobs
		if job & jobs:
			#print "Matched this job:", job & jobs
			score = 50 * len(job & jobs)
		return score
	
	def test_websites():
		score = 0
		web = set([person.get('website')])
		web.add(person.get('github_url'))
		#print "GitHub profile website:", web
		webs = set(data.get('websites').values())
		#print "LinkedIn profile websites:", webs
		if web & webs:
			#print "Matched this website:", web & webs
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


def print_results(devs):	
	for dev in devs:
		if dev['li_matches']:
			if dev['li_matches'][0]['score'] >= 75:
				msg = "YES (%d): %s" % (dev['li_matches'][0]['score'] ,dev.get('name'))
				f.writelines(msg + '\n')
				print msg
			elif dev['li_matches'][0]['score'] >= 0:
				msg = "MAYBE (%d): %s" % (dev['li_matches'][0]['score'] ,dev.get('name'))
				f.writelines(msg + '\n')
				print msg
			else:
				msg = "NO (%d): %s" % (dev['li_matches'][0]['score'] ,dev.get('name'))
				f.writelines(msg + '\n')
				print msg
		else:
			msg = "NO (n/a): %s" % dev.get('name')
			f.writelines(msg + '\n')
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



if __name__ == '__main__':
	devs, log = setup()
	with open(log, 'w') as f:
		
		# Use Google to find potential LinkedIn matches
		for dev in devs:
			print'\rGoogling for matches for %s...' % dev.get('name')
			dev['li_matches'] = get_matching_li_profiles(dev)
		print "Done.\n"
		
		# Compare the LinkedIn profiles to the GitHub, score them and sort them. Return best at index[0]
		for dev in devs:
			print '\rEvaluating matches for %s...' % dev.get('name')
			dev['li_matches'] = evaluate_li_matches(dev)
		print "Done.\n"
			
		# test website parsing
		#check_li_parsing_and_matching(devs):	

		# Use Pipl to match remainder
		for dev in [dev for dev in devs if dev['email']]:
			if dev['li_matches']:
				if dev['li_matches'][0]['score'] < 75:
					result = try_piplsearch(dev)
					if result:
						dev['li_matches'].append(result)
						# re-sort from highest scoring match to lowest
						dev['li_matches'] = sorted(dev['li_matches'], key =lambda k: k['score'], reverse=True)
			else:
				result = try_piplsearch(dev)
				if result:
					dev['li_matches'].append(result)
					# re-sort from highest scoring match to lowest
					dev['li_matches'] = sorted(dev['li_matches'], key =lambda k: k['score'], reverse=True)
			
		# See the results of running through both algos
		print_results(devs)
					
		"""
		# print the results of 
		print '\n********************\n'
		print 'RESULTS OF APPLYING TWO MATCHING ALGORITHMS\n'
		for dev in devs:
			if person['linkedin']:
				print "YES for %s." % person.get('name')
			else:
				print "NO for %s." % person.get('name')
		"""
