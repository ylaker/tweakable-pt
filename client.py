#! /usr/bin/python

import logging
import threading
import importlib
import json
import os

from pyptlib.client import ClientTransportPlugin
from pyptlib.config import EnvError

from twisted.internet import reactor, protocol

from EventQueue import EventQueue

class TransportLaunchException(Exception):
    pass

def launchPT(name):
    """
    Launch the Pluggable Transport
    """
    if name != 'twkbl':
        raise TransportLaunchException(\
            'Tried to launch unsupported transport %s' % name)

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    #Loading the config file
    try:
        config = json.load(open(DIRNAME + '/config/config_client.json'))
    except Exception as e:
        logging.warning(str(e))

    #Assert whether the config structure is as expected
    if not isinstance(config['Components'], list):
        raise Exception("Malformed config file")

    comps = []
    
    #Loop over the config for each component
    for comp_config in config['Components']:

        #Assert validity of the config
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

        #Instanciate the component and add it to the list
        try:
            comps.append(comp_class(comp_config, "client", queue))
        except Exception as e:
            logging.warning(str(e))

        #Specific behaviour to retreive the address where the pt is listenning 
        #for conn from the tor client 
        if comp_config['name'] == "Upstream":
            return_addr = (comp_config['host'], comp_config['port'])

    #Start all components
    for component in comps:
        component.start()

    #Return the host and port where upstream connection should be made
    return return_addr
    

def main():
    logging.basicConfig(\
        filename=DIRNAME + '/log/tweakable_client.log', \
        filemode='w', \
        level=logging.DEBUG)
    logging.debug("test")
    
    client = ClientTransportPlugin()

    #Try to init pyptlib pluggin for the client for each transport
    try:
        client.init(supported_transports = ["twkbl"])
    except EnvError, err:
        logging.warning("pyptlib could not bootstrap ('%s')." % str(err))

    #Try to launch each transport
    for transport in client.getTransports():
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
    DIRNAME = os.path.dirname(os.path.realpath(__file__))
    main()