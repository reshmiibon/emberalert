from datetime import datetime
from Services import Notification
import DataManager
import DataPurger
import DataRetriever
import schedule
import time


# schedule the purger once a week
schedule.every(1).weeks.do(DataPurger.purge_data)

db_delay = 15
print(f'Sleeping for {db_delay} seconds to wait for database to startup', flush=True)
time.sleep(db_delay)


# infinite loop to keep the scheduler running
while True:
    generation_time = datetime.now()

    # add engine run
    run_id = -1
    try:
        run_id = DataManager.execute_write_stored_procedure("add_engine_run", [generation_time])[0][0][0]
    except Exception as e:
        print(f'There was an issue adding an engine run to the database. {e}', flush=True)

    print(f'The engine run id is: {run_id}', flush=True)

    retrieved = False

    # Run the data retriever
    try:
        DataRetriever.run(run_id)
        retrieved = True
    except Exception as e:
        print(f'There was an issue with the data retrieval process. {e}', flush=True)
        DataPurger.remove_failed_run()

    # Run the notification service
    try:
        if retrieved:
            Notification.handle_notify_users(0.7)
    except Exception as e:
        print(f'There was an issue with the notification service. {e}', flush=True)

    # Run the notification service
    try:
        if retrieved:
            DataManager.execute_write_stored_procedure("update_active")
    except Exception as e:
        print(f'There was an issue with setting the active values. {e}', flush=True)

    # schedule the purger
    schedule.run_pending()
    time.sleep(21600)   # Sleep for 6 hours
