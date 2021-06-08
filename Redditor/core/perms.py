# Redditor permisson system
# Goals: Have a class that can handle communication with a DB, tell wheter the command can run, etc

# Perms:
# allow - can use the command
# deny - can't use the command
# view - can see the command
# hidden - can't see the command

# Fields
# group - guild/role/user
# guild - allways id
# role - id if group is role
# user - if if group is user

class PermsManager:
    def __init__(self, DB, aDB) -> None:
        self.DB = DB
        # self.DB.cursor.execute('CREATE TABLE IF NOT EXISTS prefixes (id INTEGER PRIMARY KEY, prefix TEXT)')
        self.DB.connection.commit()
        self.aDB = aDB