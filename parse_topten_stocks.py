from __future__ import print_function

import json
import urllib
import boto3
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter
from pdfminer.layout import LAParams
from io import BytesIO
import os
import re
import datetime

s3 = boto3.resource('s3')

def lambda_handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    s3_new_arrived_filename = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    print('Reading file ' + s3_new_arrived_filename + ' from S3')
    extracted_results_from_pdf = '/tmp/extract.xml'
    downloaded_pdf_file = '/tmp/input.pdf'
    s3.meta.client.download_file(bucket, s3_new_arrived_filename, downloaded_pdf_file)
    print('Downloaded file ' + s3_new_arrived_filename + ' from S3')

    # convert data from pdf file to xml
    resource_mgr = PDFResourceManager()
    retstr = BytesIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = XMLConverter(resource_mgr, retstr, codec=codec, laparams=laparams)
    maxpages = 0
    caching = True
    pagenos=set()
    infile_pdf_fp = file(downloaded_pdf_file, 'rb')
    interpreter = PDFPageInterpreter(resource_mgr, device)
    for page in PDFPage.get_pages(infile_pdf_fp, pagenos, maxpages=maxpages, password='', caching=caching, check_extractable=True):
        interpreter.process_page(page)

    data = retstr.getvalue()
    device.close()
    retstr.close()
    
    # write xml (extracted from pdf) to a new file
    print('Opening file ' + extracted_results_from_pdf + ' to write extracted xml from ' + s3_new_arrived_filename)
    outfile_xml_fp = file(extracted_results_from_pdf, 'w')
    print('Opened file ' + extracted_results_from_pdf)
    outfile_xml_fp.write(data)
    outfile_xml_fp.close()
    filename_without_folderprefix_and_ext = re.sub(r'.*/','',os.path.splitext(s3_new_arrived_filename)[0])
    extracted_xml_filename_in_s3 = 'xml/' + filename_without_folderprefix_and_ext + '.xml'
    s3.meta.client.upload_file(extracted_results_from_pdf, bucket, extracted_xml_filename_in_s3)

    message = {"topten_trader_xml_filepath" : extracted_xml_filename_in_s3}
    sns_client = boto3.client('sns', region_name='us-east-1')
    sns_response = sns_client.publish(
        TargetArn='arn:aws:sns:us-east-1:898821117686:stock_data_extracted',
        Message=json.dumps({'default': json.dumps(message)}),
        Subject='Stock Buy Recommendations ' + str(datetime.date.today()),
        MessageStructure='json'
    )
