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
	dcap = dict(DesiredCapabilities.PHANTOMJS)
	dcap['phantomjs.page.settings.userAgent'] = (\
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53 "
		"(KHTML, like Gecko) Chrome/15.0.87"
		)
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
	#if len(li_profiles) == 0:
		#print "NO EXACT MATCHES FOUND FOR %s." % gh_name
	return li_profiles


def parse_a_li_profile(pub_url, fullname):
	"""
	Parses a LinkedIn profile page and returns the fields as structured data.
	"""
	def get_li_public_page(pub_url, fullname):
		page = ""
		dcap = dict(DesiredCapabilities.PHANTOMJS)
		dcap['phantomjs.page.settings.userAgent'] = (\
			"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53 "
			"(KHTML, like Gecko) Chrome/15.0.87"
			)
		driver = webdriver.PhantomJS(desired_capabilities=dcap)
		#driver = webdriver.PhantomJS()
		driver.get(pub_url)
		try:
			WebDriverWait(driver, 5).until(EC.title_contains(fullname))
			page = driver.page_source
		except:
			#print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,fullname)
			return
		finally:
			driver.quit()
		with open('Data/page.html', 'w') as f:
			f.write(page)
		return page
	
	def get_headline():
		full = ''
		title = ''
		employer = ''
		
		if soup.find("p", class_="headline title"):
			headline = soup.find("p", class_="headline title").string
			if ' at ' in headline:
				full = headline
				title, employer = full.split(' at ')
			else:
				full = title = headline
				
			profile['headline']['full'] = full
			profile['headline']['title'] = title
			profile['headline']['employer'] = employer
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
		if soup.find("span", class_="locality"):
			profile['location'] = soup.find("span", class_="locality").string
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
		experience = []
		
		jobs = soup.find_all("li", class_="position")
		for job in jobs:
			position = {'company name': '', 'company page': '', 'company logo': '',
						'title': '', 'description': '', 'start': '', 'stop': ''}
			
			if job.find("h5", class_="item-subtitle"):
				company_name = job.find("h5", class_="item-subtitle").string
				position['company name'] = company_name
			
			if job.find("h5", class_="item-subtitle").find("a"):
				company_li_page = job.find("h5", class_="item-subtitle").find("a")['href']
				position['company page'] = company_li_page
			
			if job.find("h5", class_="logo"):
				company_logo = job.find("h5", class_="logo").find("a")['href']
				position['company logo'] = company_logo
			
			if job.find("h4", class_="item-title"):
				job_title = job.find("h4", class_="item-title").string
				position['title'] = job_title
			
			if job.find("p", class_="description"):
				job_description = job.find("p", class_="description").string
				position['description'] = job_description
			
			if job.find("span", class_="date-range"):
				dates = job.find("span", class_="date-range").get_text()
				start, stop = dates.split(unichr(8211))
				stop = stop[:stop.find('(')]
				position['start'] = start.strip()
				position['stop'] = stop.strip()
				
			experience.append(position)
		return experience
	
	def get_education():
		education = []
		
		schools = soup.find_all("li", class_="school")
		for school in schools:
			edu = {'school name': '', 'school page': '', 'school logo': '',
						'degree': '', 'description': '', 'start': '', 'stop': ''}
						
			if school.find("h4", class_="item-title"):
				school_name = school.find("h4", class_="item-title").string
				edu['school name'] = school_name
				
			if school.find("h4", class_="item-title").find("a"):
				school_li_page = school.find("h4", class_="item-title").find("a")['href']
				edu['school page'] = school_li_page
				
			if school.find("h5", class_="logo"):
				school_logo = school.find("h5", class_="logo").find("a")['href']
				edu['school logo'] = school_logo
				
			if school.find("h5", class_="item-subtitle"):
				degree = school.find("h5", class_="item-subtitle").string
				edu['degree'] = degree
				
			if school.find("div", class_="description"):
				school_description = school.find("div", class_="description").find("p").string
				edu['description'] = school_description
				
			if school.find("span", class_="date-range"):
				dates = school.find("span", class_="date-range").get_text()
				start, stop = dates.split(unichr(8211))
				#stop = stop[:stop.find('(')]
				edu['start'] = start.strip()
				edu['stop'] = stop.strip()
				
			education.append(edu)
		return education
	
	def get_publications():
		publications =[]
		
		pubs = soup.find_all("li", class_="publication")
		for pub in pubs:
			publication = {'title': '', 'journal': '', 'date': '', 'description': '', 
							'contributors': []}
			
			if pub.find("h4", class_="item-title"):
				publication['title'] = pub.find("h4", class_="item-title").string
				
			if pub.find("h5", class_="item-subtitle"):
				publication['journal'] = pub.find("h5", class_="item-subtitle").string
				
			if pub.find("span", class_="date-range"):
				publication['date'] = pub.find("span", class_="date-range").find("time").string
				
			if pub.find("p",class_="description"):
				text = pub.find("p", class_="description").string
				publication['description'] =  text
				
			if pub.find_all("li", class_="contributor"):
				contributors = pub.find_all("li", class_="contributor")
				for contributor in contributors:
					if contributor.string:
						publication['contributors'].append(contributor.string)
					if contributor.find("a"):
						publication['contributors'].append(contributor.find("a").string)
			
			publications.append(publication)
		return publications
	
	def get_photo():
		photo_url = ''
		if soup.find("img", class_="image photo lazy-loaded"):
			photo_url = soup.find("img", class_="image photo lazy-loaded")['src']
		return photo_url
	
	def get_languages():
		languages =[]
		langs = soup.find_all("li", class_="language")
		for lang in langs:
			language ={'name': '', 'proficiency': ''}
			
			if lang.find("h4", class_="name"):
				language['name'] = lang.find("h4", class_="name").string
			
			if lang.find("p", class_="proficiency"):
				language['proficiency'] = lang.find("p", class_="proficiency").string
			
			languages.append(language)
		return languages
	
	def get_skills():
		skills_list = []
		skills = soup.find_all("li", class_="skill")
		#skills.extend(soup.find_all("li", class_="skill extra"))
		for skill in skills:
			if skill.find("a"):
				skills_list.append(skill.a['title'])
		return skills_list
	
	def get_summary():
		pdb.set_trace()
		summary = ''
		if soup.find("section", id="summary"):
			summary = soup.find("section", id="summary").p.string
		return summary
	
	def get_recommendation():
		recommendations = []
		recs = soup.find_all("li", class_="recommendation-container")
		for rec in recs:
			if rec.find("blockquote", class_="recommendation"):
				recommendations.append(rec.blockquote.string)
		return recommendations
	
	# parsed LinkedIn profile will be returned as a dict
	profile = { 'canonical_url': '', 'name': '', 'headline': {},'location': {}, 
				'photo_url': '','employment': [], 'education': [], 'publications': [], 
				'websites': {}, 'skills':[], 'languages': [], 'summary': ''}
	
	# parse the LinkedIn profile
	page = get_li_public_page(pub_url, fullname)
	if page:
		soup = BeautifulSoup(page, 'html5lib')
		get_canonical_url()
		get_name()
		get_headline()
		get_location()
		profile['photo_url'] = get_photo()
		profile['employment'] = get_employment()
		profile['education'] = get_education()
		get_websites()
		profile['publications'] = get_publications()
		profile['languages'] = get_languages()
		profile['skills'] = get_skills()
		# profile['summary'] = get_summary()
		# get_recommendations()
	return profile


def evaluate_li_matches(person):
	""" score each potential match """
	for match in person['li_matches']:
		potential_match = parse_a_li_profile(match.get('url'), person.get('name'))
		if potential_match.get('name'):
			match['score'] = score_li_matches(person, potential_match)
			match['parsed_profile'] = potential_match
		else:
			match['score'] = -1	# unable to parse the LinkedIn page
	
	# sort from highest scoring match to lowest
	person['li_matches'] = sorted(person['li_matches'], key =lambda k: k['score'], reverse=True)
	return dev['li_matches']


def score_li_matches(gh, li):
	def test_location():
		score = 0
		if gh.get('city') in li.get('location'):
			#print "Matched location: ", github_location 
			score = 25
		return score
	
	def test_employment_old():
		score = 0
		job = set(map(normalize,[gh.get('company')]))
		job.discard(None)	# to avoid a match if both the GiHub and LinkedIn profiles have no employer listed.
		#print "GitHub profile employer:", job
		if li.get('employment'):
			#pdb.set_trace()
			jobs = set(map(normalize,[position['company name'] for position in li['employment']]))
			#print "LinkedIn profile employers:", jobs
		if job & jobs:
			#print "Matched this job:", job & jobs
			score = 50 * len(job & jobs)
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
			# todo: match email and personal website domain against LinkedIn employment history.
		else:
			# we have nothing in GitHub we can use to match agaist LinkedIn employment history.
			pass
			
		return score
	
	def test_websites():
		score = 0
		web = set([gh.get('website')])
		web.add(gh.get('github_url'))
		#print "GitHub profile website:", web
		webs = set(li.get('websites').values())
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



if __name__ == '__main__':
	reload(sys)
	sys.setdefaultencoding('utf-8')
	devs, log = setup()
	
	"""
	# Use Google to find potential LinkedIn matches
	for dev in devs:
		try:
			print'\rGoogling for matches for %s...' % dev.get('name')
			dev['li_matches'] = get_matching_li_profiles(dev)
		except:
			print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,dev['name'])
			continue
	utils.save_as_json(devs, 'googlesearchresults')
	print "Done.\n"
	#raw_input('Continue?')
	"""
	
	# Compare the LinkedIn profiles to the GitHub, score them and sort them. Return best at index[0]
	devs = utils.load_json('googlesearchresults')
	for dev in devs:
		print '\rEvaluating matches for %s...' % dev.get('name')
		dev['li_matches'] = evaluate_li_matches(dev)
	utils.save_as_json(devs, 'scoredresults')
	print "Done.\n"
	#raw_input('Continue?')
				
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
	

