import logging

from twisted.internet import reactor, protocol

class DownstreamProtocol(protocol.Protocol):
    """Downstream protocol. Between the two Pluggable Transport"""
    def __init__(self, network_component):
        self.network_component = network_component

    def connectionMade(self):
        self.network_component.conn_condition.acquire()
        self.network_component.connection = self
        self.network_component.conn_condition.notify()
        self.network_component.conn_condition.release()
    
    def dataReceived(self, data):
        self.network_component.data_from_connection(data)
    
    def connectionLost(self, reason):
        logging.warning("Downstream: Connection lost (%s)." % \
            reason.getErrorMessage())
        self.transport.loseConnection()

    def connectionFailed(self, reason):
        logging.warning("Downstream: Connection failed (%s)." % \
            reason.getErrorMessage())
        self.transport.loseConnection()

#Factory for the downstream protocol
class DownstreamFactory(protocol.ClientFactory):
    """ Downstream factory """#
    def __init__(self, network_component):
        self.network_component = network_component

    def buildProtocol(self, addr):
        return DownstreamProtocol(self.network_component)

    def clientConnectionFailed(self, connector, reason):
        logging.warning("Downstream: Connection failed - goodbye! (%s)." % \
            reason.getErrorMessage())

    
    def clientConnectionLost(self, connector, reason):
        logging.warning("Downstream : Connection lost - goodbye! (%s)." % \
            reason.getErrorMessage())
        
