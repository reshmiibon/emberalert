import sys
import os
fpath = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.pardir
))
sys.path.append(fpath)
import DataManager
import messages


def handle_opt_in(latitude, longitude, phone_number): 
    try:
        phone_number = phone_number.replace('-', '')
        DataManager.execute_write_stored_procedure("add_user", [latitude, longitude, phone_number])
        messages.send_opt_in_message(phone_number)
        return True
    except Exception as e:
        print(e)
        return False

def handle_opt_out(phone_number):
    try:
        phone_number.replace('-', '')
        DataManager.execute_write_stored_procedure("remove_user", [phone_number])
        messages.send_opt_out_message(phone_number)
        return True
    except Exception as e:
        print(e)
        return False

def handle_notify_users(minimum_distance):
    result = DataManager.execute_read_stored_procedure("get_users_near_fire", [minimum_distance])
    for row in result[0]:
        dist_km = round((111139 * row[1])/1000,0)
        if(dist_km < 50):
            messages.send_message(row[0], ("URGENT: Emberalert has detected a potential wildfire that is predicted to " 
                                  f"be within {dist_km}km in the next 24 hours. Please check with local authorities to see if an "
                                    "evacuation order has been issued"))
        elif(dist_km < 200):
            messages.send_message(row[0], ("WARNING: Emberalert has detected a potential wildfire that is predicted to " 
                                  + f"be within {dist_km}km in the next 24 hours. Please check with local authorities for more "
                                  + "information"))
        else:
            messages.send_message(row[0], ("NOTE: Emberalert has detected a potential wildfire that is predicted to be "
                                 + f"within {dist_km}km in the next 24 hours. Please check with local authorities for more "
                                 + "information"))