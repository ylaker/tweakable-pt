#! /usr/bin/python

import sys
import logging

from pyptlib.client import ClientTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

import socks5


class TransportLaunchException(Exception):

    pass


def launchPT(name):
    """
    Launch the Pluggable Transport
    """
    if name != 'simple':
        raise TransportLaunchException('Tried to launch unsupported transport %s'
                 % name)

    #Upstream host and port, where the PT is listenning for connection.
    up_host = '127.0.0.1'
    up_port = 9151

    #Downstream host and port, where the PT is connecting on the other side. 
    down_host = '127.0.0.1'
    down_port = 9045

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
            else:
                logging.warning("Connection manager not ready")
           
        def connectionLost(self, reason):
            logging.warning("Downstream : Connection lost (%s)." % \
                            reason.getErrorMessage())
            self.close()
    
        def connectionFailed(self, reason):
            logging.warning("Downstream: Connection failed (%s)." % \
                            reason.getErrorMessage())
            self.close()

    #Protocol for the upstream connection, based on a protocol for a socks5 server
    class UpstreamProtocol(socks5.SOCKSv5Protocol):
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

    #Factory for the upstream protocol
    class UpstreamFactory(socks5.SOCKSv5Factory):
        """
        A SOCKSv5 Factory.
        """
        def __init__(self, conn_manager):
            self.conn_manager = conn_manager

        def startFactory(self):
            logging.debug("Upstream: Starting up SOCKS server factory.")

        def buildProtocol(self, addr):
            return UpstreamProtocol(conn_manager, reactor)

    #Connection manager is created
    conn_manager = ConnectionManager()

    #Upstream listenner is launched
    try:
        up_fact = UpstreamFactory(conn_manager)
        addrport = reactor.listenTCP(up_port, up_fact, interface=up_host)
    except Exception, e:
        logging.warning("UpstreamInit: %s" %e)

    #Downstream connection
    try:
        down_fact = DownstreamFactory(conn_manager)
        reactor.connectTCP(down_host, down_port, down_fact)
    except Exception, e:
        logging.warning("DownstreamInit: %s" %e)

    #Return the host and port where upstream connection should be made
    return (addrport.getHost().host, addrport.getHost().port)
    

def main():
    logging.basicConfig(filename='pt-client.log',filemode='w', level=logging.DEBUG)

    transports = ["simple"]
    client = ClientTransportPlugin()
        
    #Try to init pyptlib pluggin for the client for each transport
    for transport in transports:
        try:
            client.init(transport)
        except EnvError, err:
            logging.warning("pyptlib could not bootstrap ('%s')." % str(err))

    #Try to launch each transport
    for transport in transports:
        try:
            addrport = launchPT(transport)
            client.reportMethodSuccess(transport, "socks5", addrport, None)
        except TransportLaunchException:
            logging.warning('Failed to launch' + str(transport))
            client.reportMethodError(transport, 'Failed to launch')

    #Report end and launch reactor when transports are launched
    client.reportMethodsEnd()
    reactor.run()

if __name__ == '__main__':
    main()