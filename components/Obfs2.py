import logging
import threading

import random
import hashlib
import argparse

import Obfsproxy.aes as aes
import Obfsproxy.serialize as srlz
import Obfsproxy.rand as rand

from Base import BasicComponent

MAGIC_VALUE = 0x2BF5CA7E
SEED_LENGTH = 16
MAX_PADDING = 8192
HASH_ITERATIONS = 100000

KEYLEN = 16  # is the length of the key used by E(K,s) -- that is, 16.
IVLEN = 16  # is the length of the IV used by E(K,s) -- that is, 16.

ST_WAIT_FOR_KEY = 0
ST_WAIT_FOR_PADDING = 1
ST_OPEN = 2

def h(x):
    """ H(x) is SHA256 of x. """

    hasher = hashlib.sha256()
    hasher.update(x)
    return hasher.digest()

def hn(x, n):
    """ H^n(x) is H(x) called iteratively n times. """

    data = x
    for _ in xrange(n):
        data = h(data)
    return data

class Obfs2Component(BasicComponent):
    """
    Obfs2Component implements the obfs2 protocol
    """
    def __init__(self, config, mode, queue):
        dest_endpoint = (config['dest_above'], config['dest_below'])

        BasicComponent.__init__(self, config['ID'], dest_endpoint, mode, queue)

    def process_events(self):
        """
        Process events arriving from the queue
        """

        rsp = True
        for key in sorted(self.incomming_events):
            #Process each event 
            incomming_event = self.incomming_events.pop(key)
            
            if incomming_event.source_ID == self.dest_below:
                endpoint = self.dest_above
            elif incomming_event.source_ID == self.dest_above:
                endpoint = self.dest_below
            else:
                raise Exception("Received event from unknown endpoint")

            outgoing_event = self.create_event(incomming_event.event_type, \
                                            endpoint, incomming_event.payload)
            
            #Gather information about sending each event
            ret = self.send_event(outgoing_event)
            rsp = rsp and ret

        #Evaluate if it is succesful
        if not rsp:
            raise Exception("Failed to process an event")
        return rsp

if __name__ == '__main__':
    pass