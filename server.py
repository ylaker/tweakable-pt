#! /usr/bin/python

import logging
import threading

from pyptlib.server import ServerTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

import Connectivity.Downstream as Downstream
import Connectivity.Upstream as Upstream

from TweakableComponents.EventQueue import EventQueue
from TweakableComponents.NetworkComponent import NetworkComponent


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

    up_host, up_port = or_port

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    upstream_component = NetworkComponent(1, 2, queue)
    downstream_component = NetworkComponent(2, 1, queue)

    upstream_component.start()
    downstream_component.start()

    #Listenner for downstream connection is launched
    try:
        down_fact = Downstream.DownstreamFactory(downstream_component)
        addrport = reactor.listenTCP(down_port, down_fact, interface = down_host)
    except Exception, e:
        logging.warning("Downstream: %s" % e)

    #Upstream connection is created
    try:
        up_fact = Upstream.UpstreamServerFactory(upstream_component)
        reactor.connectTCP(up_host, up_port, up_fact)
    except Exception, e:
        logging.warning("Upstream: %s" %e)
    
    #Return the host and port where the PT is listenning for downstream connection
    return (addrport.getHost().host, addrport.getHost().port)
    
def main():
    logging.basicConfig(filename='server.log',filemode='w', level=logging.DEBUG)

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
    