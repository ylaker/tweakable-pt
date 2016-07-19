import logging

from twisted.internet import reactor, protocol

class DownstreamProtocol(protocol.Protocol):
    """CLient standard protocol"""
    def __init__(self, conn_manager):
        self.conn_manager = conn_manager

    def connectionMade(self):
        self.conn_manager.set_downstream_conn(self)
    
    def dataReceived(self, data):
        if self.conn_manager.is_ready():
            self.conn_manager.upstream_conn.transport.write(data)
    
    def connectionLost(self, reason):
        logging.warning("Downstream: Connection lost (%s)." % \
            reason.getErrorMessage())
        self.close()

    def connectionFailed(self, reason):
        logging.warning("Downstream: Connection failed (%s)." % \
            reason.getErrorMessage())
        self.close()

#Factory for the downstream protocol
class DownstreamFactory(protocol.ClientFactory):
    """ Client factory """

    def __init__(self, conn_manager):
        self.conn_manager = conn_manager

    def buildProtocol(self, addr):
        return DownstreamProtocol(self.conn_manager)

    def clientConnectionFailed(self, connector, reason):
        logging.warning("Downstream: Connection failed - goodbye! (%s)." % \
            reason.getErrorMessage())
    
    def clientConnectionLost(self, connector, reason):
        logging.warning("Downstream : Connection lost - goodbye! (%s)." % \
            reason.getErrorMessage())
        reactor.stop()