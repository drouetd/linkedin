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
			query = parameters.get('email').lower()
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
			print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,query)
			return
		finally:
			driver.quit()
		return html
	
	def follow_link(url):
		""" Opens the passed url and returns the html. """
		prefix = "https://pipl.com/search/"
		html = ''
		
		if url[:3] == '/rd':
			pass
		else:
			url = prefix + url
			driver = webdriver.PhantomJS()
			driver.get(url)
		
			# retrieve the results page
			try:
				WebDriverWait(driver, 5).until(EC.title_contains(params.get('email')))
				html = driver.page_source
			except:
				print "%s occurred while processing: %s" % (sys.exc_info()[0].__name__,params.get('email'))
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
	
	def initial_parse(html):
		# email search: check that there is a page to parse
		if params.get('email') and html:
			soup = BeautifulSoup(html, "html5lib")
			pc_bottom = soup.find("div", id="profile_container_bottom")
			
			# we get desired profile page directly
			if pc_bottom:
				parse_pc_bottom(pc_bottom)
			
			# we get a list of matching profiles
			elif soup.find("div", id="match_results"):
				# use "ddonayo@yahoo.com" on pipl site to see an example.
				groups = soup.find("div", id="match_results").find_all("div", class_="profile_result group")
				for group in groups:
					link_to_follow = group.find("div", class_="title truncate").a['href']
					html = follow_link(link_to_follow)
					initial_parse(html)
			# no matches
			else:
				pass
		# futur: add username search and name + location search
		else:
			pass
		return
	
	def parse_pc_bottom(htmlblock):
		groups = htmlblock.find_all("div", class_="person_result group")
		if groups:
			for group in groups:
				site_url = clean_url(group.find("div", class_="person_content").a['href'])
				site_name = group.find("div", class_="line2 truncate").find("span").string
				site_name = site_name[site_name.find("-") + 1:].strip()
				socmedia.append({'site_name': site_name, 'url': site_url})
		return
	
	
	socmedia = []
	URL = "https://pipl.com"
	
	page = submit_query(URL, params)
	initial_parse(page)
	return socmedia


if __name__ == "__main__":
	
	#parameters = {'email': 'drouetd@gmail.com'}
	#parameters = {'name': 'daniel drouet', 'location': 'montreal'}
	parameters = {'email': None}
	with open('Data/mtl100email.csv', 'r') as csvfile:
		f = csv.reader(csvfile)
		for row in f:
			parameters['email'] = row[5]
			results = pipl_search(parameters)
			if [socmedia for socmedia in results if socmedia['site_name']=='LinkedIn']:
			#if any('LinkedIn' in socmedia for socmedia in results):
				print "FOUND LINKEDIN for %s." % row[0], "Also:", [dic['site_name'] for dic in results]
			else:
				print "NO LINKEDIN for %s." % row[0], "Also:", [dic['site_name'] for dic in results]

