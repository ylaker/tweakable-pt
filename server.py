#! /usr/bin/python

import logging
import threading
import importlib
import json

from pyptlib.server import ServerTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

from EventQueue import EventQueue

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

    up_host, up_port = or_port

    logging.debug(transport_bindaddr)

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    logging.debug("logging")
    try:
        config = json.load(open('Config/config_server.json'))
    except Exception as e:
        logging.warning(str(e))
    logging.debug(str(config))

    comps = []
    
    for comp_config in config['Components']:

        if not isinstance(comp_config['name'], unicode) or \
                not isinstance(comp_config['module'], unicode) or \
                not isinstance(comp_config['class'], unicode):
            raise Exception("Malformed config file")

        try:    
            mod = importlib.import_module(comp_config['module'])
            comp_class = getattr(mod, comp_config['class'])
        except Exception as e:
            logging.warning(str(e))
        logging.debug("imported")

        if comp_config['name'] == "Upstream":
            comp_config['host'] = unicode(up_host)
            comp_config['port'] = up_port

        try:    
            comps.append(comp_class(comp_config, "server", queue))
        except Exception as e:
            logging.warning(str(e))

        if comp_config['name'] == "Downstream":
            return_addr = (comp_config['host'], comp_config['port'])

    logging.debug("configured")
    logging.debug(comps)

    for component in comps:
        component.start()

    logging.debug("started")
    #Return the host and port where the PT is listenning for downstream connection
    return return_addr
    
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
            addrport = launchPT(transport, transport_bindaddr, \
                                bridge.config.getORPort())
            bridge.reportMethodSuccess(transport, transport_bindaddr, None)
        except TransportLaunchException:
            logging.warning('Failed to launch' + str(transport))
            bridge.reportMethodError(transport, 'Failed to launch')

    #Report end and run the reactor
    bridge.reportMethodsEnd()
    reactor.run()

if __name__ == '__main__':
    main()
    