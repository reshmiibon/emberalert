import requests

BASE_URL = "http://localhost:5000"

def test_opt_in(phoneNumber, latitude, longitude):
    url = BASE_URL + '/notification/process-opt-in'
    data = {'latitude': latitude, 'longitude': longitude, 'phone': phoneNumber}
    return requests.post(url, json=data)

def test_opt_out(phone_number):
    url = BASE_URL + '/notification/process-opt-out'
    data = {'phone_number' : phone_number}
    return requests.post(url, json=data)

# TESTS:
assert('success' in test_opt_in('7055390360', '23.2222', '-21.98').json())
assert('success' in test_opt_out('7055390360'))