from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer
from main import app


if __name__ == '__main__':
    server = WSGIServer(('', 5000), app.wsgi_app)
    server.serve_forever()