#! /usr/bin/python

import sys
import logging

from pyptlib.server import ServerTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

BUFFER_SIZE = 4096

class TransportLaunchException(Exception):

    pass

def launchPT(transport, transport_bindaddr, or_port):
    """
    Launch the Puggable Transport
    """
    if transport != 'simple':
        raise TransportLaunchException('Tried to launch unsupported transport %s'
                 % transport)

    #Downstream host and port where the client will try to connect 
    down_host = '127.0.0.1'
    down_port = 9045

    #Upstream host and port where the traffic will be forwarded. Tor OR port.
    up_host, up_port = or_port

    #Connection manager used to link and relay data between upstream and 
    #downstream connections.
    class ConnectionManager():
        def __init__(self):
            self.downstream_conn = None
            self.upstream_conn = None

        def set_upstream_conn(self, conn):
            self.upstream_conn = conn

        def set_downstream_conn(self, conn):
            self.downstream_conn = conn

        def is_ready(self):
            return self.downstream_conn and self.upstream_conn

    #Protocol for the downstream connection
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
    class DownstreamFactory(protocol.Factory):
        """ Server factory """
        def __init__(self, conn_manager):
            self.conn_manager = conn_manager

        def buildProtocol(self, addr):
            return DownstreamProtocol(self.conn_manager)

    #Protocol for the upstream connection
    class UpstreamProtocol(protocol.Protocol):
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
    class UpstreamFactory(protocol.ClientFactory):
        """ Server factory """
        def __init__(self, conn_manager):
            self.conn_manager = conn_manager

        def buildProtocol(self, addr):
            return UpstreamProtocol(self.conn_manager)

    #Connection manager is created
    conn_manager = ConnectionManager()

    #Listenner for downstream connection is launched
    try:
        down_fact = DownstreamFactory(conn_manager)
        addrport = reactor.listenTCP(down_port, down_fact, interface = down_host)
    except Exception, e:
        logging.warning("Downstream: %s" % e)

    #Upstream connection is created
    try:
        up_fact = UpstreamFactory(conn_manager)
        reactor.connectTCP(up_host, up_port, up_fact)
    except Exception, e:
        logging.warning("Upstream: %s" %e)
    
    #Return the host and port where the PT is listenning for downstream connection
    return (addrport.getHost().host, addrport.getHost().port)
    
def main():
    logging.basicConfig(filename='pt-server.log',filemode='w', level=logging.DEBUG)

    #Init the pyptlib plugin
    bridge = ServerTransportPlugin()
    try:
        bridge.init(["simple"])
    except EnvError, err:
        logging.warning("pyptlib could not bootstrap ('%s')." % str(err))

    #Launch the transports
    for transport, transport_bindaddr in bridge.getBindAddresses().items():
        try:
            addrport = launchPT(transport, transport_bindaddr, bridge.config.getORPort())
            bridge.reportMethodSuccess(transport, transport_bindaddr, None)
        except TransportLaunchException:
            logging.warning('Failed to launch' + str(transport))
            bridge.reportMethodError(transport, 'Failed to launch')

    #Report end and run the reactor
    bridge.reportMethodsEnd()
    reactor.run()

if __name__ == '__main__':
    main()
    