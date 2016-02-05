#!/usr/bin/env python

import csv
import sys
import urllib
import pdb
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def pipl_search(params):
	"""
	Use the pipl.com service to find the social media profiles of a person 
	when all we have is an email address, a username or their name and location.
	"""
	def submit_query(url=None, parameters=None):
		"""
		Completes and submits the form, then returns the results page html.
		"""
		query = ""
		#service_args = ['--proxy=1120.52.73.5:8080', '--proxy-type=https']
		
		# get the form elements
		#driver = webdriver.PhantomJS(service_args=service_args)
		driver = webdriver.PhantomJS()
		driver.get(url)
		input_box_all = driver.find_element_by_id("findall")
		input_box_location = driver.find_element_by_id("findlocation")
		search_button = driver.find_element_by_id("search_button")
		
		# set up non-location query parameters. Only uses one; combining confuses Pipl.com
		if parameters.get('email'):
			query = parameters.get('email')
			input_box_all.send_keys(query)
		if parameters.get('name'):
			query = parameters.get('name')
			input_box_all.send_keys(query)
		if parameters.get('username'):
			query = parameters.get('username')
			input_box_all.send_keys(query)
			
		# set up location query parameters
		if parameters.get('location'):
			input_box_location.send_keys(parameters.get('location'))
			
		#submit the query
		search_button.submit()
		
		# retrieve the results page
		try:
			WebDriverWait(driver, 10).until(EC.title_contains(query))
			html = driver.page_source
		except:
			print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,query)
			return
		finally:
			driver.quit()
		return html
	
	def clean_url(dirty_url):
		""" Strips redirect and tracking info from the url. """
		dirty_url = urllib.unquote(dirty_url)
		dirty_url = dirty_url[dirty_url.find('http'):]
		if dirty_url.find('&'):
			clean_url = dirty_url[:dirty_url.find('&')]
		else:
			clean_url = dirty_url
		return clean_url
	
	
	socmedia = []
	URL = "https://pipl.com"
	
	page = submit_query(URL, params)
	# parsing depends on type of search: email vs name + location
	# check that there is a page to parse
	if params.get('email') and page:
		soup = BeautifulSoup(page, "html5lib")
		pc_bottom = soup.find("div", id="profile_container_bottom")
		match = soup.find("div", id="match_results")
		if pc_bottom:
			groups = pc_bottom.find_all("div", class_="person_result group")
			if groups:
				for group in groups:
					site_url = clean_url(group.a['href'])
					site_name = group.find("div", class_="line2 truncate").find("span").string
					site_name = site_name[site_name.find("-") + 1:].strip()
					socmedia.append({site_name: site_url})
		elif match:
			# use "ddonayo@yahoo.com" on pipl site to see an example.
			pass
	else:
		pass
		
	return socmedia


if __name__ == "__main__":
	
	#parameters = {'email': 'drouetd@gmail.com'}
	#parameters = {'name': 'daniel drouet', 'location': 'montreal'}
	parameters = {'email': None}
	with open('Data/mtl30email.csv', 'r') as csvfile:
		f = csv.reader(csvfile)
		for row in f:
			parameters['email'] = row[5]
			results = pipl_search(parameters)
			if any('LinkedIn' in socmedia for socmedia in results):
				print "FOUND LINKEDIN for %s" % row[0]
			else:
				print "NO LINKEDIN for %s" % row[0]

