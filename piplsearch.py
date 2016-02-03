#!/usr/bin/env python

import sys
import re
import urllib
from urlparse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def submit_query(url=None, parameters=None):
	"""
	Completes and submits a form, then returns the results page html.
	"""
	query = ""
	
	# get the form elements
	driver = webdriver.PhantomJS()
	driver.get(url)
	input_box_all = driver.find_element_by_id("findall")
	input_box_location = driver.find_element_by_id("findlocation")
	search_button = driver.find_element_by_id("search_button")
	
	print parameters
	raw_input("Enter to continue")
	
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
		WebDriverWait(driver, 5).until(EC.title_contains(query))
		html = driver.page_source
	except:
		return
	finally:
		driver.quit()
	return html


def pipl_search(params):
	"""
	Use the pipl.com service to find the social media profiles of a person 
	when all we have is an email address, a username or their name and location.
	"""
	def clean_url(dirty_url):
		""" Strips redirect and tracking info. """
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
	if params.get('email'):
		soup = BeautifulSoup(page, "html5lib")
		pc_bottom = soup.find("div", id="profile_container_bottom")
		if pc_bottom:
			groups = pc_bottom.find_all("div", class_="person_result group")
			if groups:
				print "Lenght of Groups: %d" % len(groups)
				for group in groups:
					site_url = clean_url(group.a['href'])
					print "site url: %s" % site_url
					site_name = group.find("div", class_="line2 truncate").find("span").string
					site_name = site_name[site_name.find("-") + 1:].strip()
					socmedia.append({site_name: site_url})
	else:
		pass
		
	return socmedia


if __name__ == "__main__":
	"""
	pipl = "https://pipl.com"
	params = {"email": "drouetd@gmail.com"}
	
	page = submit_query(pipl, params)
	print page
	"""
	parameters = {'email': 'drouetd@gmail.com'}
	#parameters = {'name': 'daniel drouet', 'location': 'montreal'}
	results = pipl_search(parameters)
	print '\n', results
