#!/usr/bin/env python

import urllib
from urlparse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pdb

def parse_li_profile(public_url, fullname):
	"""
	Wrapper around the parser. Fetches the LinkedIn page
	 and feeds the html to the parser.
	"""
	page = ""
	dcap = dict(DesiredCapabilities.PHANTOMJS)
	dcap['phantomjs.page.settings.userAgent'] = ("Mozilla/5.0 (X11; Linux x86_64) \
			AppleWebKit/53 " "(KHTML, like Gecko) Chrome/15.0.87")
	driver = webdriver.PhantomJS(desired_capabilities=dcap)
	#driver = webdriver.PhantomJS()
	driver.get(public_url)
	try:
		WebDriverWait(driver, 5).until(EC.title_contains(fullname))
		page = driver.page_source
		filename = 'Data/soup_' + fullname.replace(' ', '') + '.html'
		with open(filename, 'w') as f:
			f.write(page)
	except:
		#print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,fullname)
		return
	finally:
		driver.quit()
	return liparser(page)


def liparser(page):
	"""
	Receives a public LinkedIn profile page as raw html and returns the fields as structured data.
	"""
	def get_headline():
		head = {'full': '', 'title': '', 'employer': ''}
		if soup.find("p", class_="headline title"):
			headline = soup.find("p", class_="headline title").string
			if ' at ' in headline:
				head['full'] = headline
				head['title'], head['employer'] = headline.split(' at ')
			else:
				head['full'] = head['title'] = headline
		return head
	
	def get_canonical_url():
		url = ''
		if soup.find("link", rel="canonical"):
			url = soup.find("link", rel="canonical")['href']
		return url
	
	def get_name():
		name = ''
		if soup.find("h1", id="name"):
			name = soup.find("h1", id="name").string
		return name
	
	def get_location():
		location = ''
		if soup.find("span", class_="locality"):
			location = soup.find("span", class_="locality").string
		return location
	
	def get_websites():
		def clean_urls(dirty_url):
			""" Strip protocol and trailing '/' from blog info profided by GitHub profile"""
			url = urlparse(dirty_url)
			if url.path == '/':
				clean_url = url.netloc
			else:
				clean_url = url.netloc + url.path
			return clean_url
		
		
		webs = {}
		company_num = 1    # handle multiple company websites
		table = soup.find("div", class_="profile-overview").find("table", class_="extra-info")
		if table.find("tr", class_="websites"):
			websites = table.find("tr", class_="websites").find_all("a")
			for site in websites:
				# if multiple company websites are listed append a number to the key, i.e. "Company Website 1"
				if site.string == "Company Website":
					key = "Company Website" + str(company_num)
					company_num += 1
				else:
					key = site.string 
				
				# strip the redirect and tracking info from urls
				url = urllib.unquote(str(site))
				start = url.find('?url=') + 5
				stop = url.rfind('&amp;urlhash')
				clean_url = clean_urls(url[start:stop])
				webs[key] = clean_url
		return webs
	
	def get_employment():
		experience = []
		
		jobs = soup.find_all("li", class_="position")
		for job in jobs:
			position = {'company name': '', 'company page': '', 'company logo': '',
						'title': '', 'description': '', 'start': '', 'stop': ''}
			
			if job.find("h5", class_="item-subtitle"):
				position['company name'] = job.find("h5", class_="item-subtitle").string
			
			if job.find("h5", class_="item-subtitle").find("a"):
				position['company page'] = job.find("h5", class_="item-subtitle").find("a")['href']
			
			if job.find("h5", class_="logo"):
				position['company logo'] = job.find("h5", class_="logo").find("a")['href']
			
			if job.find("h4", class_="item-title"):
				position['title'] = job.find("h4", class_="item-title").string
			
			if job.find("p", class_="description"):
				position['description'] = job.find("p", class_="description").string
			
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
				edu['school name'] = school.find("h4", class_="item-title").string
				
			if school.find("h4", class_="item-title").find("a"):
				edu['school page'] = school.find("h4", class_="item-title").find("a")['href']
				
			if school.find("h5", class_="logo"):
				edu['school logo'] = school.find("h5", class_="logo").find("a")['href']
				
			if school.find("h5", class_="item-subtitle"):
				edu['degree'] = school.find("h5", class_="item-subtitle").string
				
			if school.find("div", class_="description"):
				edu['description'] = school.find("div", class_="description").find("p").string
				
			if school.find("span", class_="date-range"):
				dates = school.find("span", class_="date-range").get_text()
				start, stop = dates.split(unichr(8211))
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
				publication['description'] = pub.find("p", class_="description").string
				
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
		for skill in skills:
			if skill.find("a"):
				skills_list.append(skill.a['title'])
		return skills_list
	
	def get_summary():
		summary = ''
		if soup.find("section", id="summary"):
			summary = unicode(soup.find("section", id="summary").find("p"))
			summary = summary.replace('<p>', '')
			summary = summary.replace('</p>', '')
			summary = summary.replace('<br/>', '\n')
		return summary
	
	def get_recommendations():
		recommendations = []
		recs = soup.find_all("li", class_="recommendation-container")
		for rec in recs:
			if rec.find("blockquote", class_="recommendation"):
				recommendations.append(rec.blockquote.string)
		return recommendations
	
	
	# parsed LinkedIn profile will be returned as a dict
	profile = { 'canonical_url': '', 'name': '', 'headline': {},'location': {}, 
				'photo_url': '','employment': [], 'education': [], 'publications': [], 
				'websites': {}, 'skills':[], 'languages': [], 'summary': '', 
				'recommendations': []}
	
	# parse the LinkedIn profile
	if page:
		soup = BeautifulSoup(page, 'html5lib')
		profile['canonical_url'] = get_canonical_url()
		profile['name'] = get_name()
		profile['headline'] = get_headline()
		profile['location'] = get_location()
		profile['photo_url'] = get_photo()
		profile['employment'] = get_employment()
		profile['education'] = get_education()
		profile['websites'] = get_websites()
		profile['publications'] = get_publications()
		profile['languages'] = get_languages()
		profile['skills'] = get_skills()
		profile['summary'] = get_summary()
		profile['recommendations'] = get_recommendations()
	return profile

