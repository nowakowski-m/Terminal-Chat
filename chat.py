# Terminal-chat executable file.

import functions as f

# Usage:               host, username, password
mydb = f.connect_to_db('localhost', 'root', '')

app = f.App(mydb)
app.start_app()
app.app()

mydb.close()