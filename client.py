#! /usr/bin/python

import logging
import threading

from pyptlib.client import ClientTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

import Connectivity.Downstream as Downstream
import Connectivity.Upstream as Upstream

from TweakableComponents.EventQueue import EventQueue
from TweakableComponents.NetworkComponent import NetworkComponent
from TweakableComponents.DummyComponent import DummyComponent


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

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    upstream_component = NetworkComponent(3, (-1, 4), queue)
    dummy_component = DummyComponent(4, (3, 5), queue)
    downstream_component = NetworkComponent(5, (4, -1), queue)

    upstream_component.start()
    dummy_component.start()
    downstream_component.start()

    #Upstream listenner is launched
    try:
        up_fact = Upstream.UpstreamClientFactory(upstream_component)
        addrport = reactor.listenTCP(up_port, up_fact, interface=up_host)
    except Exception, e:
        logging.warning("UpstreamInit: %s" %e)

    #Downstream connection
    try:
        down_fact = Downstream.DownstreamFactory(downstream_component)
        reactor.connectTCP(down_host, down_port, down_fact)
    except Exception, e:
        logging.warning("DownstreamInit: %s" %e)

    #Return the host and port where upstream connection should be made
    return (addrport.getHost().host, addrport.getHost().port)
    

def main():
    logging.basicConfig(filename='client.log',filemode='w', level=logging.DEBUG)
    
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