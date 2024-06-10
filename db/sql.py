INSERT_PROCESS="INSERT INTO process (name, items) VALUES (%s, %s)"
GET_PROCESS="SELECT id, name, start_time, end_time, status FROM process"
GET_PROCESS_BY_ID="SELECT * FROM process WHERE id = %s"
START_PROCCES="UPDATE process SET start_time = %s, status = 2 WHERE id = %s"
GET_SETTINGS="SELECT * FROM settings"

