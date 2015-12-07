from flask import Flask
import umysqldb
umysqldb.install_as_MySQLdb()
from flask_peewee.db import Database
from config import Configuration

app = Flask(__name__)
app.config.from_object(Configuration)

db = Database(app)
