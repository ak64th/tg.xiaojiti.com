class Configuration(object):
    DATABASE = {
        'name': 'group_int.db',
        'engine': 'peewee.SqliteDatabase',
        'threadlocals': True,
    }
    DEBUG = True
    SECRET_KEY = 'bf1edf6b2d0f3a91f9d7d55d51e89e5779bb1e579bee'