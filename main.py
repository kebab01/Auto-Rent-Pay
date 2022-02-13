import requests
import json
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import logging
import traceback
load_dotenv()

RENT = os.getenv("RENT")
ACCOM_URL = 'https://apply-accom.uow.edu.au'
ONESTOP_URL = 'https://uow.onestopsecure.com'

loginPayload = {
	"invalidCredentialsMessage":"The credentials provided are invalid. Please double check your email address and password are entered correctly.",
	'pageID': 16,
	'password': os.getenv('PASS'),
	'rememberLogin': False,
	'returnUrl': "/StarRezPortalX/016A544F/8/9/Home-Home",
	'username': os.getenv("EMAIL")
}

headers={
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:97.0) Gecko/20100101 Firefox/97.0',
	'Accept':'*/*',
	'Accept-Language':'en-US,en;q=0.5',
	'Accept-Encoding':'gzip, deflate',
	'Content-Type':'application/json; charset=utf-8',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Length':'294',
	'Origin':'https://apply-accom.uow.edu.au',
	'__requestverificationtoken':'',
	'Referer':'https://apply-accom.uow.edu.au/StarRezPortalX/Login?returnUrl=%2FStarRezPortalX%2F016A544F%2F8%2F9%2FHome-Home',
	'Sec-Fetch-Dest':'empty',
	'Sec-Fetch-Mode':'cors',
	'Sec-Fetch-Site':'same-origin',
	'Te':'trailers',
	'Connection':'close'
  }
proxies={
	'http':'http://127.0.0.1:8080',
	'https':'http://127.0.0.1:8080'
}

def login(session):

	#Get verification token
	url = f'{ACCOM_URL}/StarRezPortalX/General/Register/register/Login'
	logging.info(f'Making GET request login page {url}')
	r = session.get(url)

	if r.status_code != 200:
		failedStatus(r, url, session)

	soup = BeautifulSoup(r.content, 'html.parser')
	headers['__requestverificationtoken'] = soup.find_all('input')[-1].get('value')

	if headers['__requestverificationtoken'] == None:
		logging.critical("Could not find requestverificationtoken so therefore cannot procceed")
		exit()

	logging.info(f"Successfully found requestverificationtoken - {headers['__requestverificationtoken']}")

	#Login to accom portal
	logging.info(f"Attempting to login to accomadation portal")
	r = session.post(loginPost, data=json.dumps(loginPayload), headers=headers)

	if r.status_code != 200:
		failedStatus(r, url, session)

def verifyAmount(session):
	url = f'{ACCOM_URL}/StarRezPortalX/7FFC185B/18/23/Accounts-Account_Summary'
	r = session.get(url)

	soup = BeautifulSoup(r.content, 'html.parser')
	soup = soup.find("div", {"data-fieldname":"TotalToPay"})
	amount = soup.find('input').get('value')
	logging.info(f"Requested payment {amount}")

	if amount != RENT:
		logging.critical(f"Invalid amount found. Requested payment of {amount} when expected {RENT}")
		exit()

def failedStatus(r, url, session):

	logging.critical(f"Server responded with error code {r.status_code}, therefore cannot continue")
	logging.info(f"URL requested {url}")
	logging.ingo(f"Cookies {session.cookies}")
	exit()

def prepareDetails(session):

	#Prepare payment details
	paymentDetails = {
		'EPS_MERCHANT':'',
		'EPS_TXNTYPE':'',
		'EPS_REFERENCEID':'',
		'EPS_AMOUNT':'',
		'EPS_TIMESTAMP':'',
		'EPS_FINGERPRINT':'',
		'EPS_RESULTPARAMS':'',
		'EPS_REDIRECT':'',
		'EPS_RESULTURL':'',
		'EPS_PAYMENTCHOICE':'',
		'EPS_CALLBACKURL':'',
		'EPS_CALLBACKPARAMS':'',
		'EPS_CARDNUMBER':'',
		'EPS_EXPIRYMONTH':'',
		'EPS_EXPIRYYEAR':'',
		'EPS_CCV':'',
	}

	#Get iframe which contains payment information
	logging.info('Preparing payment details')
	soup = BeautifulSoup(r.content, 'html.parser')
	iframe = soup.find('iframe').get('src')
	iframe = session.get(iframe)
	soup = BeautifulSoup(iframe.content, 'html.parser')
	attributes = soup.find_all('input')

	for attr in attributes:
		paymentDetails[attr.get('name')] = attr.get('value')

	paymentDetails['EPS_CARDNUMBER'] = os.getenv('CARD_NUM')
	paymentDetails['EPS_EXPIRYMONTH'] = os.getenv('CARD_EXP_MONTH')
	paymentDetails['EPS_EXPIRYYEAR'] = os.getenv('CARD_EXP_YEAR')
	paymentDetails['EPS_CCV'] = os.getenv('CARD_CCV')

	return paymentDetails

def makePayment(session):
	#Make payment to uni
	logging.info("Sending payment")

	url = 'https://transact.nab.com.au/live/directpostv2/authorise'
	r = session.post(url, data=paymentDetails, allow_redirects=True)
	
	if r.status_code != 200:
		failedStatus(r, url, session)

	logging.info("Checking if Successfull...")

	soup = BeautifulSoup(r.content, 'html.parser')
	links = soup.find_all('a')

	for item in links:
		if 'apply-accom.uow.edu.au' in item.get('href'):
			link = item.get('href')
			return link

def main():
	logging.basicConfig(filename="payment.log", level=logging.INFO, format='%(levelname)s - %(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	logging.info("-------------Starting new instance-------------")
	with requests.session() as session:

		try:

			login(session)

			#Start payment process
			verifyAmount(session)
			logging.info("Preparing to make payment")
			payData={"amount":RENT,"pageID":23}

			url = f'{ACCOM_URL}/StarRezPortalX/General/Accounts/accounts/PayAll'
			r = session.post(url, headers=headers, data=json.dumps(payData))

			data={
				"PageWidgetData":[],
				"ManualBreakup":False,
				"AmountToPay":"0.00",
				"TotalToPay":RENT
			}

			url = f'{ACCOM_URL}/StarRezPortalX/7FFC185B/18/23/Accounts-Account_Summary'
			r = session.post(url, headers=headers, data=json.dumps(data))

			url = f'{ACCOM_URL}/StarRezPortalX/DA6BAD6B/18/25/Accounts-Shopping_Cart_Checko'
			cartPage = session.post(, headers=headers, data=json.dumps({'PageWidgetData':[]})).text.strip('"')
			r= session.get(f'{ACCOM_URL}{cartPage}')

			data = {
				'UDS_FREIGHT_INDEX': '', 
				'UDS_CART_SUB_TOTAL': f'${RENT}',
				'UDS_ACTION': 'CPPPB'
			}

			logging.info("Navigating to onestopsecure for payment")

			url = f'{ONESTOP_URL}/onestopweb/StarRezAccommodation/viewcart'
			r = session.post(url, data=data)

			url = f'{ONESTOP_URL}/onestopweb/student/paymentemail?UDS_ACTION=PMPBPN'
			r = session.get(url)

			if r.status_code != 200:
				failedStatus(r, url, session)

			paymentDetails = prepareDetails(session)
			
			#Check payment is of correct amount
			if paymentDetails['EPS_AMOUNT'] != RENT:
				logging.critical(f"There was a descrepency in expected payment. Expected {payData['amount']}, Got {paymentDetails['EPS_AMOUNT']}, exiting...")
				exit()

			#Send payment
			link = makePayment(session)

			#Check if successfull
			r = session.get(link)

			if status_code != 200:
				failedStatus(r, url, session)

			if 'Payment Unsuccessful!' in r.text:
				print("Payment was Unsuccessful")
				logging.error("Payment was Unsuccessful")
			else:
				print("Payment was Successfull")
				logging.info("Payment was Successfull!!")

			with open('index.html', 'w') as f:
				f.write(str(r.text))
		except:
			logging.critical(f"An error occurred, {traceback.format_exc()}")
			exit(1)

def test():

	try:
		raise Exception
	except:
		print(traceback.format_exc())

if __name__ == "__main__":
	main()





