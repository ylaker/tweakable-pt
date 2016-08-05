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

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    #Loading the config file
    try:
        config = json.load(open(\
            '/home/yoann/MscInfoSec-Project/tweakable_pt/Config/config_server.json'))
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

        #Instantiate the component and add it to the list
        try:    
            comps.append(comp_class(comp_config, "server", queue))
        except Exception as e:
            logging.warning(str(e))

        #Specific behaviour to retrieve the address where it will listen for pt conn
        if comp_config['name'] == "Downstream":
            return_addr = (comp_config['host'], comp_config['port'])

    #Starting all the components
    for component in comps:
        component.start()

    #Return the host and port where the PT is listenning for downstream connection
    return return_addr
    
def main():
    logging.basicConfig(\
        filename='/home/yoann/MscInfoSec-Project/tweakable_pt/server.log', \
        filemode='w', \
        level=logging.DEBUG)
    logging.debug("test")

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
    