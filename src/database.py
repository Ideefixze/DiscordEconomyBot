import sqlite3

CURRENCY = "ZS"

#Initial connection and creation of nescessary tables in the Database if they don't exist yet
dbconnect = sqlite3.connect('database.db')
print("Database connection established...")
dbconnect.execute(
'''
CREATE TABLE IF NOT EXISTS Teams (
    id INTEGER PRIMARY KEY,
    name NVARCHAR(50),
    funds INTEGER,
    closed BOOLEAN DEFAULT 0,
    channel INTEGER
);
 ''')

dbconnect.execute(
'''
CREATE TABLE IF NOT EXISTS Players (
    id INTEGER PRIMARY KEY,
    name NVARCHAR(50),
    team_id INTEGER,
    FOREIGN KEY (team_id)
        REFERENCES Teams (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);''')
dbconnect.commit()

#Other functions
def team_by_team_name(name):
    c = dbconnect.cursor()
    c.execute(f"SELECT * FROM Teams WHERE name=\'{name}\'")
    fetch = c.fetchone()
    c.close()
    return fetch

def team_by_team_id(id):
    c = dbconnect.cursor()
    c.execute(f"SELECT * FROM Teams WHERE id={id}")
    fetch = c.fetchone()
    c.close()
    return fetch


def team_by_player_id(id):
    c = dbconnect.cursor()
    c.execute(f"SELECT T.* FROM Players P JOIN Teams T ON P.team_id=T.id WHERE P.id={id}")
    fetch = c.fetchone()
    c.close()
    return fetch

def all_team_members(t_id):
    c = dbconnect.cursor()
    c.execute(f"SELECT name FROM Players WHERE team_id={t_id}")
    fetch = c.fetchall()
    c.close()
    return fetch

def player_by_player_id(id):
    c = dbconnect.cursor()
    c.execute(f"SELECT * FROM Players WHERE id={id}")
    fetch = c.fetchone()
    c.close()
    return fetch

async def set_team_closed(val, id):
    if val:
        dbconnect.execute(f"UPDATE Teams SET closed = false WHERE id={id}")
    else:
        dbconnect.execute(f"UPDATE Teams SET closed = true WHERE id={id}")
    dbconnect.commit()

