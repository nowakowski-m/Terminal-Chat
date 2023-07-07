# Terminal-chat executable file.

import functions as f

# Usage:               host, username, password
mydb = f.connect_to_db('localhost', 'root', '')
cursor = mydb.cursor()
# Usage:       USE Database
cursor.execute("USE chat;")

app = f.App(cursor)
app.start_app()
app.app()

mydb.close()