import pdb
import requests
from bs4 import BeautifulSoup
import os
import json
import re
import constant
import datetime
import MySQLdb 
import pandas as pd

db = MySQLdb.connect(
    host = "localhost",
    user = "root",
    passwd = "12345678",
    database = "olx" 
)


class OLX:

	DOMAIN = 'https://www.olx.com.pk'
	URL = 'https://www.olx.com.pk/tablets_c1455'

	def __init__(self):
		global con 
		con = db.cursor()
		global alread_processed 
		alread_processed = []
		records = con.execute("select listing_url from tablets")
		tpl = con.fetchall()
		for d in tpl: alread_processed.append(d[0])

	def connect_to(self , url):
		payload = {}

		print(url)
		headers = {
			"Authority": "www.olx.com.pk",
			"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"98\", \"Google Chrome\";v=\"98\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Linux\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en-US,en;q=0.9"
		}

		re = requests.get(url, headers=headers ,data=payload)
		return re

	def connect_next_page(self , url , cookie):
		payload = {}

		print(url)
		headers = {
			"Authority": "www.olx.com.pk",
			"Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"98\", \"Google Chrome\";v=\"98\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Linux\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en-US,en;q=0.9",
            "cookie": cookie
		}

		re = requests.get(url, headers=headers ,data=payload)
		return re	


	def get_html(self , response):
		return BeautifulSoup(response.text , "html.parser")


	def get_links(self ,response):
		body = self.get_html(response)
		data = body.select('li[aria-label="Listing"]')
		links = []
		for link in body.select('li[aria-label="Listing"]'): links.append(self.DOMAIN + link.select_one('a').get('href'))
		return links

	def prepare_date(self ,date):
		if "hour" in date or "minute" in date:
			return datetime.datetime.now().date().isoformat()
		elif "day" in date:
			days = int(date.split()[0])
			dat = datetime.datetime.now() - datetime.timedelta(days=days)
			return dat.date().isoformat()
		elif "week" in date:
			days = int(date.split()[0]) * 7
			dat = datetime.datetime.now() - datetime.timedelta(days=days)
			return dat.date().isoformat()
		elif "month" in date:
			days = int(date.split()[0]) * 30
			dat = datetime.datetime.now() - datetime.timedelta(days=days)
			return dat.date().isoformat()
		else:
			return None	

	def parser(self ,links):
		data_array = []
		for link in links:
			
			if link in alread_processed:
				continue
			response = self.connect_to(link)
			body = self.get_html(response)
			json_data = json.loads(body.select_one('script[type="application/ld+json"]').text)
			data_hash = {}
			data_hash['title'] = json_data['name']
			data_hash['description'] = json_data['description']
			data_hash['listing_id'] = json_data['sku']
			data_hash['price'] = [d for d in body.select_one('div[aria-label="Overview"]').select('span') if 'Rs' in d.text][0].text.replace('Rs' , '').strip()
			data_hash['product_condition'] = [d for d in body.select_one('div[aria-label="Details and description"]').select('span') if 'Condition' in d.text][0].next_element.next_element.text
			data_hash['product_type'] =  [d for d in body.select_one('div[aria-label="Details and description"]').select('span') if 'Type' in d.text][0].next_element.next_element.text
			data_hash['listing_url'] = link 
			data_hash['seller_name'] = body.select_one('div[aria-label="Seller description"]').select('span')[1].text
			data_hash['is_featured'] = True if body.select_one('div[aria-label="Gallery"]').select_one('span').text == "Featured" else False
			data_hash['listing_date'] = self.prepare_date(body.select_one('span[aria-label="Creation date"]').text)
			data_array.append(data_hash)
		return data_array

	def insert_data(self , records):
		insert_query = " INSERT IGNORE INTO tablets (title , description , listing_id , price , product_condition , product_type , listing_url , seller_name , is_featured , listing_date) VALUES (%(title)s , %(description)s , %(listing_id)s , %(price)s , %(product_condition)s , %(product_type)s , %(listing_url)s , %(seller_name)s , %(is_featured)s , %(listing_date)s);"
		con.executemany(insert_query , records)
		db.commit()

	def scraper(self):
		
		response = self.connect_to(self.URL)
		cookie = response.headers['Set-Cookie']
		records = self.parser(self.get_links(response))
		self.insert_data(records)

		while(True):
			body = self.get_html(response)
			try:
				next_page = self.DOMAIN + [d for d in body.select('a') if '?page=' in d.get('href')][0].get('href')
			except Exception as e:
				print(e)
				break
			response = self.connect_next_page(next_page , cookie)
			records = self.parser(self.get_links(response))
			self.insert_data(records)

	def export_csv(self):
		sql_query = pd.read_sql('select * from olx.tablets',db)
		df = pd.DataFrame(sql_query)
		df.to_csv (r'/home/wahab/olx_scraper/results.csv', index = False)

try:
	#OLX().scraper()
	OLX().export_csv()
except Exception as e:
	print(e)
finally:
	con.close()
	db.close()

