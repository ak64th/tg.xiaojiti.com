from flask import Flask
from config import Configuration

app = Flask(__name__)
app.config.from_object(Configuration)

if app.config['DATABASE']['engine'] == 'peewee.MySQLDatabase':
    import umysqldb
    umysqldb.install_as_MySQLdb()

from flask_peewee.db import Database

db = Database(app)
