Uses three Lambda functions, S3, SNS, SES & Python (first function triggered by S3 upload; next two via SNS). 

Every week i get a PDF mailer from CabotWealth.com with 10 recommended stocks. My parser extracts data from this PDF and verifies the stocks’ rating with two more investing agencies. I get an email with stock ticker and buy price for stocks recommended positively by all three
