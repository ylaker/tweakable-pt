#! /usr/bin/python

import logging
import threading
import importlib
import json
import os

from pyptlib.server import ServerTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

from EventQueue import EventQueue

class TransportLaunchException(Exception):

    pass

def launchPT(transport, transport_bindaddr, or_port):
    """
    Launch the Puggable Transport
    """
    if transport != 'twkbl':
        raise TransportLaunchException('Tried to launch unsupported transport %s'
                 % transport)

    up_host, up_port = or_port
    down_host, down_port = transport_bindaddr

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    #Loading the config file
    try:
        config = json.load(open(DIRNAME + '/config/config_server.json'))
    except Exception as e:
        logging.warning(str(e))

    #Assert whether the config structure is as expected
    if not isinstance(config['Components'], list):
        raise Exception("Malformed config file")

    comps = []
    
    #Loop over the config for each component
    for comp_config in config['Components']:    

        #Assert validity of each config
        if not isinstance(comp_config['name'], unicode) or \
                not isinstance(comp_config['module'], unicode) or \
                not isinstance(comp_config['class'], unicode):
            raise Exception("Malformed config file")

        #Import the appropriate module and retrieve the class
        try:    
            mod = importlib.import_module(comp_config['module'])
            comp_class = getattr(mod, comp_config['class'])
        except Exception as e:
            logging.warning(str(e))

        #Specific behaviour to add the OR host and OR port retrieved from tor
        if comp_config['name'] == "Upstream":
            comp_config['host'] = unicode(up_host)
            comp_config['port'] = up_port

        #Specific behaviour to add address where the pt will listen for connection
        if comp_config['name'] == "Downstream":
            comp_config['host'] = unicode(down_host)
            comp_config['port'] = down_port

        #Instantiate the component and add it to the list
        try:    
            comps.append(comp_class(comp_config, "server", queue))
        except Exception as e:
            logging.warning(str(e))

    #Starting all the components
    for component in comps:
        component.start()

    #Return the host and port where the PT is listenning for downstream connection
    return transport_bindaddr
    
def main():
    logging.basicConfig(\
        filename=DIRNAME + '/log/tweakable_server.log', \
        filemode='w', \
        level=logging.DEBUG)
    logging.debug("test")

    #Init the pyptlib plugin
    bridge = ServerTransportPlugin()

    try:
        bridge.init(["twkbl"])
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
    BUFFER_SIZE = 4096
    DIRNAME = os.path.dirname(os.path.realpath(__file__))
    main()
    