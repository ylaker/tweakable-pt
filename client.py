#! /usr/bin/python

import logging
import threading
import importlib
import json

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
    if name != 'simple':
        raise TransportLaunchException(\
            'Tried to launch unsupported transport %s' % name)

    #Creating the queue
    add_event_condition = threading.Condition()
    queue = EventQueue(add_event_condition)

    try:
        config = json.load(open('Config/config_client.json'))
    except Exception as e:
        logging.warning(str(e))

    if not isinstance(config['Components'], list):
        raise Exception("Malformed config file")

    comps = []
    
    for comp_config in config['Components']:

        if not isinstance(comp_config['name'], unicode) or \
                not isinstance(comp_config['module'], unicode) or \
                not isinstance(comp_config['class'], unicode):
            raise Exception("Malformed config file")

        mod = importlib.import_module(comp_config['module'])
        comp_class = getattr(mod, comp_config['class'])

        comps.append(comp_class(comp_config, "client", queue))

        if comp_config['name'] == "Upstream":
            return_addr = (comp_config['host'], comp_config['port'])

    for component in comps:
        component.start()

    #Return the host and port where upstream connection should be made
    return return_addr
    

def main():
    logging.basicConfig(filename='client.log',filemode='w', \
                        level=logging.DEBUG)
    
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