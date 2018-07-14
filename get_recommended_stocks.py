from __future__ import print_function

from lxml import etree
import json
import urllib
import boto3
from io import BytesIO
import os
import re

s3 = boto3.resource('s3')

def lambda_handler(event, context):

	message = event['Records'][0]['Sns']['Message']
	print("Parsing SNS notification")
	message = json.loads(message)
	print("Grabbing input xml file name from message")
	input_xml_filename = message['topten_trader_xml_filepath']
	
	bucket = 'cabotreader'
	downloaded_xml_file = '/tmp/extract.xml'
	s3.meta.client.download_file(bucket, input_xml_filename, downloaded_xml_file)
    	print('Downloaded file ' + input_xml_filename + ' from S3 into ' + downloaded_xml_file)
	
	input_xml_fp = file(downloaded_xml_file, 'rb')
	xml_tree = etree.parse(input_xml_fp)
    	master_stock_ticker_list = []
    	for xml_tag_id in range(0, 43):   # e.g. 6,10, etc.
        	text_tag_nodes = xml_tree.xpath('//textbox[@id=' + str(xml_tag_id) + ']/textline/text') # Traverse nested tags
        	text_content = ""    # content of xml tags <text> concatenated to a string. Each <text> tag contains a single character. E.g. each character of the phrase "Nvidia (NVDA)" is stored in a separate <text> tag in the extracted xml
        	for node in text_tag_nodes:     # capture text char from each <text> tag and concatenate to spit out a string "text_content"
            		if node.text is not None:
                		text_content += node.text
        	text_content = text_content[(text_content.find('(') + 1):text_content.find(')')]
        	if text_content.isupper() and len(text_content) < 5 and text_content.isalpha():     # if text_content is < 4 chars and is all uppercase, you've found your stock ticker !! Add it to master_stock_ticker_list
                	master_stock_ticker_list.append(text_content)
	print(master_stock_ticker_list)
