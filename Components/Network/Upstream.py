import logging

from twisted.internet import reactor, protocol

import socks5

#Protocol for the upstream connection, based on a protocol for a socks5 server
class UpstreamClientProtocol(socks5.SOCKSv5Protocol):
    def __init__(self, network_component, reactor=reactor):
        self.state = 0
        self.reactor = reactor
        self.other_conn = None
        self.network_component = network_component
    
    def processEstablishedData(self, data):
        try:
            self.network_component.data_from_connection(data)
        except Exception as e:
            logging.error(str(e))
    
    def connection_established(self):
        self.network_component.conn_condition.acquire()
        self.network_component.connection = self
        self.network_component.conn_condition.notify()
        self.network_component.conn_condition.release()

#Factory for the upstream protocol
class UpstreamClientFactory(socks5.SOCKSv5Factory):
    """
    A SOCKSv5 Factory.
    """
    def __init__(self, network_component):
        self.network_component = network_component

    def startFactory(self):
        pass

    def buildProtocol(self, addr):
        return UpstreamClientProtocol(self.network_component, reactor)
        
#Protocol for the upstream connection
class UpstreamServerProtocol(protocol.Protocol):
    """CLient standard protocol"""
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
        logging.warning("Upstream: Connection lost (%s)." % \
            reason.getErrorMessage())
        self.close()
    
    def connectionFailed(self, reason):
        logging.warning("Upstream: Connection failed (%s)." % \
            reason.getErrorMessage())
        self.close()

#Protocol for the upstream protocol
class UpstreamServerFactory(protocol.ClientFactory):
    """ Server factory """
    def __init__(self, network_component):
        self.network_component = network_component
    
    def buildProtocol(self, addr):
        return UpstreamServerProtocol(self.network_component)

