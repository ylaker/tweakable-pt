from twisted.internet import reactor, protocol


class ServerProtocol(protocol.Protocol):
    def connectionMade(self):
        print "Connection made"

    def dataReceived(self, data):
        print str(data)

class ServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return ServerProtocol()

server_fact = ServerFactory()

server_addrport = reactor.listenTCP(28000, server_fact,\
                                         interface = '127.0.0.1')

print "Launching reactor"
reactor.run()
