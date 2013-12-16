import service

srv = service.Service()
srv.start()

while True:
    srv.drain_events()
