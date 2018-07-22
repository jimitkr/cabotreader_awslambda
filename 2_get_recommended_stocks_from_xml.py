from __future__ import print_function

from lxml import etree
import json
import urllib
import boto3
from io import BytesIO
import os
import re
import datetime

s3 = boto3.resource('s3')

def lambda_handler(event, context):

	message = event['Records'][0]['Sns']['Message']
	print("Parsing SNS notification")
	message = json.loads(message)
	print("Grabbing input xml file name from SNS message")
	input_xml_filename = message['topten_trader_xml_filepath']
	
	bucket = 'cabotreader'
	downloaded_xml_file = '/tmp/extract.xml'
	s3.meta.client.download_file(bucket, input_xml_filename, downloaded_xml_file)
    	print('Downloaded file ' + input_xml_filename + ' from S3 into ' + downloaded_xml_file)
	
	input_xml_fp = file(downloaded_xml_file, 'rb')
	xml_tree = etree.parse(input_xml_fp)
    	master_stock_ticker_list = []
	buy_range_and_loss_limits = []
    	for xml_tag_id in range(0, 46):   # stock tickers and their prices will be found between tag ids 0 - 46
        	text_tag_nodes = xml_tree.xpath('//textbox[@id=' + str(xml_tag_id) + ']/textline/text') # Traverse nested tags
        	text_content = ""    # content of xml tags of type <text> concatenated to a string. Each <text> tag contains a single character. E.g. each character of the phrase "Nvidia (NVDA)" is stored in a separate <text> tag in the extracted xml
        	for node in text_tag_nodes:     # capture text char from each <text> tag and concatenate to spit out a string "text_content"
            		if node.text is not None:
                		text_content += node.text
		if '-' in text_content:      # Buy range and stop loss limits for each stock are found in the format 60-75 in the PDF. If two numbers have a hyphen '-' between them, it is a buy range or stop loss limit for one of the stocks. Capture this range and store into buy_range_and_loss_limits[]
			text_content_split_by_hyphen = text_content.split('-')
			try:
				buy_range_and_loss_limits.append(float(text_content_split_by_hyphen[0]))
				buy_range_and_loss_limits.append(float(text_content_split_by_hyphen[1].split('\n')[0]))
			except:
				pass  # if characters on both sides of a hyphen are not numbers, the text in concern is not a buy range or stop loss limit. Do nothing and move on
        	text_content = text_content[(text_content.find('(') + 1):text_content.find(')')]
        	if text_content.isupper() and len(text_content) < 5 and text_content.isalpha():     # if text_content is < 4 chars and is all uppercase, you've found your stock ticker !! Add it to master_stock_ticker_list
                	master_stock_ticker_list.append(text_content)
	print('Found 10 stock tickets and their buy prices with loss limits. Forwarding data to SNS topic ten_stock_tickers_extracted, to verify stock ratings with other agencies')
	message = {"recommended_stock_list": master_stock_ticker_list, "buy_range_and_loss_limits": buy_range_and_loss_limits}
	sns_client = boto3.client('sns', region_name='us-east-1')
	sns_response = sns_client.publish(
		TargetArn='arn:aws:sns:us-east-1:898821117686:ten_stock_tickers_extracted',
		Message=json.dumps({'default': json.dumps(message)}),
		Subject='Ten Recommended Stocks ' + str(datetime.date.today()),
		MessageStructure='json')
        print('SNS topic ten_stock_tickers_extracted has been notified')
