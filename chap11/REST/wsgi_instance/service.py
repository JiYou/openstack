import wsgi

class WSGIService(object):
    def __init__(self):
        self.loader = wsgi.Loader()
        self.app = self.loader.load_app()
        self.server = wsgi.Server(self.app,
                                  '0.0.0.0',
                                  8080)
    def start(self):
        self.server.start()

    def wait(self):
        self.server.wait()

    def stop(self):
        self.server.stop()

if __name__ == "__main__":
    server = WSGIService()
    server.start()
    server.wait()
   

