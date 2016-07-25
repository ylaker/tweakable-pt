import logging

from twisted.internet import reactor, protocol

import socks5

#Protocol for the upstream connection, based on a protocol for a socks5 server
class UpstreamClientProtocol(socks5.SOCKSv5Protocol):
    def __init__(self, conn_manager, reactor=reactor):
        self.reactor = reactor
        self.state = 0
        self.otherConn = None
        self.conn_manager = conn_manager
    
    def processEstablishedData(self, data):
        if self.conn_manager.is_ready():
            self.conn_manager.downstream_conn.transport.write(data)
        else:
            logging.warning("Connection manager not ready")
    
    def connection_established(self):
        self.conn_manager.set_upstream_conn(self)

#Factory for the upstream protocol
class UpstreamClientFactory(socks5.SOCKSv5Factory):
    """
    A SOCKSv5 Factory.
    """
    def __init__(self, conn_manager):
        self.conn_manager = conn_manager
    
    def startFactory(self):
        logging.debug("Upstream client: Starting up SOCKS server factory.")
    
    def buildProtocol(self, addr):
        return UpstreamClientProtocol(self.conn_manager, reactor)
        
#Protocol for the upstream connection
class UpstreamServerProtocol(protocol.Protocol):
    """CLient standard protocol"""
    def __init__(self, conn_manager):
        self.conn_manager = conn_manager
    
    def connectionMade(self):
        self.conn_manager.set_upstream_conn(self)
    
    def dataReceived(self, data):
        if self.conn_manager.is_ready():
            self.conn_manager.downstream_conn.transport.write(data)
    
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
    def __init__(self, conn_manager):
        self.conn_manager = conn_manager
    
    def buildProtocol(self, addr):
        return UpstreamServerProtocol(self.conn_manager)

