from DataManager import execute_write_stored_procedure

def purge_data(): 
    try: 
        # Execute the data purger stored procedure
        execute_write_stored_procedure("purge_data", [7])
        print("Data purger executed successfully.")
    except Exception as e:
        print('There was an issue executing the data purger procedure')

def remove_failed_run(): 
    try: 
        # Execute the remove failed run stored procedure
        execute_write_stored_procedure("remove_failed_run")
        print("Remove failed run executed successfully.")
    except Exception as e:
        print('There was an issue executing the remove failed run procedure')
