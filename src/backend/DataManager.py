import mysql.connector
import constants

host_name = constants.DATABASE_HOST_NAME

def open_connection():
    db_connection = mysql.connector.connect(user="root", password="test", host=host_name, port=3306, database="test")
    return db_connection

def begin_transaction():
    # begin a transaction
    pass

def commit_transaction():
    # commit transaction to database
    pass

def rollback_transaction():
    # rollback the transaction
    # this will likely occur if something went awry
    pass

# params: list of arguments. if no argumments are wanted then pass an empty list 
def execute_read_stored_procedure(procedure, params=[]):
    db_connection = open_connection()

    output = []
    try:
        with db_connection.cursor() as cursor:
            cursor.callproc(procedure, params)
            
            for result in cursor.stored_results():
                output.append(result.fetchall())
    except Exception as e:
        print(e)
        raise
    finally:
        db_connection.close()

    return output


# params: list of arguments. if no argumments are wanted then pass an empty list 
def execute_write_stored_procedure(procedure, params=[]):
    db_connection = open_connection()

    output = []
    try:
        with db_connection.cursor() as cursor:
            cursor.callproc(procedure, params)

            for result in cursor.stored_results():
                output.append(result.fetchall())
            db_connection.commit()
    except Exception as e:
        print(e)
        raise
    finally:
        db_connection.close()

    return output
