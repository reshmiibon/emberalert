import requests
import constants
BASE_URL = 'https://api.twilio.com/2010-04-01/Accounts'
API_ACCOUNT_SID = constants.TWILLIO_ACCOUNT_SID
API_ACCOUNT_AUTH_TOKEN = constants.TWILLIO_ACCOUNT_AUTH_TOKEN

footer = ("\n\nNOTE: Ember-Alert does not supercede your local authorities orders. Ember-Alert uses satellite data to"
    + "detect fires and is not 100% accurate. Please check with your local authorities before taking action.")

def send_opt_in_message(phone_number):
    message = ("You're now signed up to receive alerts from EmberAlert! Please note that EmberAlert does not"
        +" replace the need to follow local government orders. \n \nTo stop receiving alerts please reply with OPTOUT")
    send_message(phone_number, message)

def send_opt_out_message(phone_number):
    message = "Opt out successful. Please let us know how we can improve by emailing us at info.emberalert@gmail.com"
    send_message(phone_number, message)

def send_message(phone_number, message):
    authInfo = requests.auth.HTTPBasicAuth(API_ACCOUNT_SID, API_ACCOUNT_AUTH_TOKEN)
    url = f'{BASE_URL}/{API_ACCOUNT_SID}/Messages'
    params = {'Body': message + footer, 'From': "+17407626065", 'To': phone_number}
    try:
        r = requests.post(url, data=params, auth=authInfo)
        if r != 201:
            assert("Message Failed to send")
    except Exception as e:
        print("ERROR: " + e)