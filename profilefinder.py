#!/usr/bin/env python
import sys
import re
import urllib
from urlparse import urlparse

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


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
		return s.lower()
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
	names = []
	
	if len(sys.argv) > 1 and sys.argv[1] == "-f":
		# we are reading from a CSV file
		with open(sys.argv[2], 'r') as f:
			lines = f.readlines()
			for line in lines:
				lst = line.strip().replace('"','').split(',')
				git_url = "github.com/" + lst[GIT_USERNAME]
				names.append({'name': unicode(lst[NAME], 'utf-8'),
				'city': unicode(lst[CITY], 'utf-8'),
				'company': normalize(unicode(lst[COMPANY], 'utf-8')),
				'website': clean_urls(unicode(lst[BLOG], 'utf-8')),
				'github_url': unicode(git_url, 'utf-8')
				})
	elif len(sys.argv) > 1 and sys.argv[1] == "-n":
		# we are looking up a single individual. Details entered at the command line
		pass 
	else:
		print('Usage:\n $ profilefinder.py -f filename #file must be in CSV format.\n $ profilefinder.py -n [name="first last" location="city" company="company name", blog="url"]')
	
	return names


def get_list_of_potential_li_profiles(fullname, city):
	"""
	Googles a name to find promising LinkedIn profiles. For exact name matches
	from the first page of results, returns the LinkedIn public profile urls in
	a list.
	"""
	profile_urls = []
	
	# perform the Google search
	driver = webdriver.PhantomJS()
	driver.get('http://www.google.com')
	input_box = driver.find_element_by_name("q")
	input_box.send_keys(fullname + " " + city + " software" + " site:linkedin.com")
	input_box.submit()
	try:
		WebDriverWait(driver, 5).until(EC.title_contains(fullname))
		page = driver.page_source
	except:
		print "Timeout googleing for %s." % fullname
		return
	finally:
		driver.quit()
	
	# parse the search results
	url_pattern = re.compile(r'q=(h.+?)&')
	soup = BeautifulSoup(page, "html5lib")
	results = soup.select('h3.r')
	for result in results:
		# test each results for exact name match
		name = result.a.get_text()
		name_cleaned_up = name[:name.find('|')].strip()
		if name_cleaned_up == fullname:
			# get the link to this LinkedIn profile
			match = re.search(url_pattern, result.a['href'])
			if match:
				profile_urls.append(match.group(1))
	
	return profile_urls


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
			#print "Timeout loading LinkedIn profile for %s." % fullname
			return
		finally:
			driver.quit()
		return page
	
	def get_headline():
		s = soup.find("div", class_="profile-overview").find("p", class_="headline title").string
		if s:
			at = s.find('at')
			profile['headline']['title'] = s[:at].strip()
			profile['headline']['employer'] = s[at + 2:].strip()
			# add the employer to profile['employment'] because people sometimes only update their headline.
			profile['employment'].append(normalize(profile['headline']['employer']))
		return
	
	def get_location():
		profile['location'] = soup.find("div", class_="profile-overview").find("span", class_="locality").string
		return
	
	def get_websites():
		company_num = 1    # handle multiple company websites
		table = soup.find("div", class_="profile-overview").find("table", class_="extra-info")
		if table.find("tr", class_="websites"):
			websites = table.find("tr", class_="websites").find_all("a")
			for site in websites:
				# handle multiple company websites being listed
				if site.string == "Company Website":
					key = "Company Website" + str(company_num)
					company_num += 1
				else:
					key = site.string 
				# strip the redirect and tracking info from urls
				url = urllib.unquote(str(site))
				start = url.find('?url=') + 5
				stop = url.rfind('&amp;urlhash')
				profile['websites'][key] = clean_urls(url[start:stop])
		return
	
	def get_employment():
		jobs = soup.find_all("li", class_="position")
		for job in jobs:
			company_name = job.find("h5", class_="item-subtitle", recursive=True).string
			profile['employment'].append(normalize(company_name))
		return
	
	
	profile = { \
			'name': {},
			'location': {},
			'employment': [],
			'headline': {},
			'websites': {},
			'photo': ''}
	
	page = get_li_public_page(pub_url, fullname)
	if page:
		soup = BeautifulSoup(page, 'html5lib')
		get_location()
		get_websites()
		get_headline()
		get_employment()
	else:
		profile = -1
	
	return profile


def validate_url(person, data):
	def test_location():
		score = 0
		pass
		return score
	
	def test_employment():
		score = 0
		job = set([person.get('company')])
		#print "GitHub profile employer:", job
		jobs = set(data.get('employment'))
		#print "LinkedIn profile employers:", jobs
		if job & jobs:
			print "Matched this job:", job & jobs
			score = 50 * len(job & jobs)
		return score
	
	def test_websites():
		score = 0
		web = set([person.get('website')])
		web.add(person.get('github_url'))
		print "GitHub profile website:", web
		webs = set(data.get('websites').values())
		print "LinkedIn profile websites:", webs
		if web & webs:
			print "Matched this website:", web & webs
			score = 100 * len(web & webs)
		return score
	
	return sum([test_location(), test_employment(), test_websites()])
	

if __name__ == '__main__':
	
	people = setup()
	for person in people:
		print '\n', person.get('name'), "(" + person.get('city') + ")" + ":"
		person['urls_to_test'] = get_list_of_potential_li_profiles(person.get('name'), person.get('city'))
		#print "URLs to test for %s: %s" % (person.get('name'), person.get('urls_to_test'))
		for url in person['urls_to_test']:
			data = parse_a_li_profile(url, person.get('name'))
			if data != -1:
				score = validate_url(person, data)
				print url, "(", score, ")"
			else:
				print url, ": UNABLE TO LOAD URL."
	