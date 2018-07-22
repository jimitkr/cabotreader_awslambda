import json
import re
import urllib2
import datetime
import boto3

def lambda_handler(event, context):
    # Check ratings of stocks on these websites
    stock_rating_service_urls = \
        [
            ["Zacks", "https://www.zacks.com/stock/quote/@ticker@"],
            ["TheStreet", "http://www.thestreet.com/quote/@ticker@.html"]
        ]
    message = event['Records'][0]['Sns']['Message']
    print('Parsing SNS notification')
    message = json.loads(message)
    print("Grabbing list of ten recommended stocks from SNS message")
    recommended_stock_list = message['recommended_stock_list']
    buy_range_and_loss_limits = message['buy_range_and_loss_limits']

    # Out of ten recommended stocks, determine which ones are rated BUY by both Zacks and TheStreet. I want to invest in a stock only if all recommendation engines rate it a BUY. Will add new recommendation services in the future

    buy_these_stocks_at_these_prices = []  # [NVDA, 201, ....]

    for ticker_index_in_master_list, ticker_value in enumerate(recommended_stock_list):
        buy_flag = False
        # Check stock's rating with other agencies. If any one agency doesn't recommend this stock, move to next ticker
        for rating_url in stock_rating_service_urls:
            actual_url_with_ticker_inserted = rating_url[1].replace("@ticker@", ticker_value)
            print('Checking consensus rating for ' + ticker_value + " @ " + actual_url_with_ticker_inserted)
            html_request = urllib2.Request(actual_url_with_ticker_inserted)
            html_request.add_header("User-Agent", "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13")
            rating_website_html_content = urllib2.urlopen(html_request).read()
            rating_website_html_content_as_string = str(rating_website_html_content)

            # check if all rating services recommend this stock positively
            if rating_url[0] == "Zacks":
                if re.findall('1-Strong Buy', rating_website_html_content_as_string) or re.findall('2-Buy', rating_website_html_content_as_string):
                    buy_flag = True
                else:
                    buy_flag = False
                    print(rating_url[0] + " does not rate " + ticker_value + " a Buy.")
		    break
            if rating_url[0] == "TheStreet":
                if re.findall(r"[AB][+-]?<sub>", rating_website_html_content_as_string):
                    buy_flag = True
                else:
                    buy_flag = False
                    print(rating_url[0] + " does not rate " + ticker_value + " a Buy.")
                    break
        # if a stock is recommended to buy, find the average buy price from its buy range. Example, if buy range of ABC is 60-70, average buy price is 65. 
        if buy_flag:
            buy_range_lower_upper_limits = []
            buy_range_lower_upper_limits.append(buy_range_and_loss_limits[4 * ticker_index_in_master_list])
            buy_range_lower_upper_limits.append(buy_range_and_loss_limits[(4 * ticker_index_in_master_list) + 1])
            buy_price = sum(buy_range_lower_upper_limits) / len(buy_range_lower_upper_limits)
            buy_these_stocks_at_these_prices.extend([ticker_value, buy_price])
    # Send email with stocks that are rated Buy by all agencies, to my email
    ses_client = boto3.client('ses')
    email_from = 'princejim87@gmail.com'
    email_to = 'princejim87@gmail.com'
    emaiL_subject = 'Stock Buy Recoommendations From CabotWealth As Of: ' + str(datetime.date.today())
    email_body = str(buy_these_stocks_at_these_prices)
    response = ses_client.send_email(
        Source = email_from,
        Destination={
            'ToAddresses': [
                email_to,
            ],
        },
        Message={
            'Subject': {
                'Data': emaiL_subject
            },
            'Body': {
                'Text': {
                    'Data': email_body
                }
            }
        }
    )
