import logging
import threading

import random
import hashlib
import argparse
import sys

import Obfsproxy.aes as aes
import Obfsproxy.serialize as srlz
import Obfsproxy.rand as rand

from Base import BasicComponent

""" 
From Obfsproxy repo:
https://github.com/david415/obfsproxy/blob/david-bananaphone/obfsproxy/common/aes.py
"""

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

        # Check if the shared_secret class attribute was already
        # instantiated. If not, instantiate it now.
        if not hasattr(self, 'shared_secret'):
            self.shared_secret = None
        # If external-mode code did not specify the number of hash
        # iterations, just use the default.
        if not hasattr(self, 'ss_hash_iterations'):
            self.ss_hash_iterations = HASH_ITERATIONS

        if self.shared_secret:
            logging.debug("Starting obfs2 with shared secret: %s" % self.shared_secret)

        # Our state.
        self.state = ST_WAIT_FOR_KEY

        if mode == "client":
            self.we_are_initiator = True
            self.setup_client()
        else:
            self.we_are_initiator = False
            self.setup_server()
            
        # Shared secret seed.
        self.secret_seed = None

        # Crypto to encrypt outgoing data.
        self.send_crypto = None
        # Crypto to encrypt outgoing padding.
        self.send_padding_crypto = None
        # Crypto to decrypt incoming data.
        self.recv_crypto = None
        # Crypto to decrypt incoming padding.
        self.recv_padding_crypto = None

        # Number of padding bytes left to read.
        self.padding_left_to_read = 0

        # If it's True, it means that we received upstream data before
        # we had the chance to set up our crypto (after receiving the
        # handshake). This means that when we set up our crypto, we
        # must remember to push the cached upstream data downstream.
        self.pending_data_to_send = False
        self.buffer = []
        
        self.handshake()

    def handshake(self):
        """
        Do the obfs2 handshake:
        SEED | E_PAD_KEY( UINT32(MAGIC_VALUE) | UINT32(PADLEN) | WR(PADLEN) )
        """
        # Generate keys for outgoing padding.
        self.send_padding_crypto = \
            self._derive_padding_crypto(self.initiator_seed if self.we_are_initiator else self.responder_seed,
                                        self.send_pad_keytype)

        padding_length = random.randint(0, MAX_PADDING)
        seed = self.initiator_seed if self.we_are_initiator else self.responder_seed

        handshake_message = seed + self.send_padding_crypto.crypt(srlz.htonl(MAGIC_VALUE) +
                                                                  srlz.htonl(padding_length) +
                                                                  rand.random_bytes(padding_length))

        logging.debug("obfs2 handshake: %s queued %d bytes (padding_length: %d).",
                  "initiator" if self.we_are_initiator else "responder",
                  len(handshake_message), padding_length)

        payload = self.create_payload(handshake_message)
        outgoing_event = self.create_event("data", \
                                        self.dest_below, payload)
        
        self.send_event(outgoing_event)

    def setup_server(self):
        """
        Setup server for the obfs2 protocol.
        The client and server differ in terms of their padding strings.
        """

        self.send_pad_keytype = 'Responder obfuscation padding'
        self.recv_pad_keytype = 'Initiator obfuscation padding'
        self.send_keytype = "Responder obfuscated data"
        self.recv_keytype = "Initiator obfuscated data"
        self.initiator_seed = None # Initiator's seed.
        self.responder_seed = rand.random_bytes(SEED_LENGTH) # Responder's seed

    def setup_client(self):
        """
        Setup client for the obfs2 protocol.
        The client and server differ in terms of their padding strings.
        """

        self.send_pad_keytype = 'Initiator obfuscation padding'
        self.recv_pad_keytype = 'Responder obfuscation padding'
        self.send_keytype = "Initiator obfuscated data"
        self.recv_keytype = "Responder obfuscated data"
        self.initiator_seed = rand.random_bytes(SEED_LENGTH) # Initiator's seed.
        self.responder_seed = None # Responder's seed.

    def receivedUpstream(self, data):
        """
        Got data from upstream. We need to obfuscated and proxy them downstream.
        """
        if not self.send_crypto:
            logging.debug("Got upstream data before doing handshake. Caching.")
            self.buffer.append(data)
            self.pending_data_to_send = True
            return

        logging.debug("obfs2 receivedUpstream: Transmitting %d bytes.", len(data))
        # Encrypt and proxy them.
        return self.send_crypto.crypt(data)
    
    def receivedDownstream(self, data):
        """
        Got data from downstream. We need to de-obfuscate them and
        proxy them upstream.
        """
        logging_prefix = "obfs2 receivedDownstream" # used in loggings

        if self.state == ST_WAIT_FOR_KEY:
            logging.debug("%s: Waiting for key." % logging_prefix)
            if len(data) < SEED_LENGTH + 8:
                logging.debug("%s: Not enough bytes for key (%d)." % (logging_prefix, len(data)))
                return data # incomplete

            if self.we_are_initiator:
                self.responder_seed = data[:SEED_LENGTH]
            else:
                self.initiator_seed = data[:SEED_LENGTH]

            logging.debug(len(data))

            data = data[SEED_LENGTH:]

            # Now that we got the other seed, let's set up our crypto.
            self.send_crypto = self._derive_crypto(self.send_keytype)
            self.recv_crypto = self._derive_crypto(self.recv_keytype)
            self.recv_padding_crypto = \
                self._derive_padding_crypto(self.responder_seed if self.we_are_initiator else self.initiator_seed,
                                            self.recv_pad_keytype)

            # XXX maybe faster with a single d() instead of two.
            magic = srlz.ntohl(self.recv_padding_crypto.crypt(data[:4]))
            padding_length = srlz.ntohl(self.recv_padding_crypto.crypt(data[4:8]))

            data = data[8:]

            logging.debug("%s: Got %d bytes of handshake data (padding_length: %d, magic: %s)" % \
                          (logging_prefix, len(data), padding_length, hex(magic)))

            if magic != MAGIC_VALUE:
                logging.warning("obfs2: Corrupted magic value '%s'" % hex(magic))
                raise Exception
            if padding_length > MAX_PADDING:
                logging.warning("obfs2: Too big padding length '%s'" % padding_length)
                raise Exception

            self.padding_left_to_read = padding_length
            self.state = ST_WAIT_FOR_PADDING

        while self.padding_left_to_read:
            #if not data: return

            n_to_drain = self.padding_left_to_read
            if (self.padding_left_to_read > len(data)):
                n_to_drain = len(data)

            data = data[n_to_drain:]
            self.padding_left_to_read -= n_to_drain
            logging.debug("%s: Consumed %d bytes of padding, %d still to come (%d).",
                      logging_prefix, n_to_drain, self.padding_left_to_read, len(data))

        self.state = ST_OPEN
        logging.debug("%s: Processing %d bytes of application data.",
                  logging_prefix, len(data))

        if self.pending_data_to_send:
            logging.debug("%s: We got pending data to send and our crypto is ready. Pushing!" % logging_prefix)
            for data in self.buffer:
                self.receivedUpstream(data) # XXX touching guts of network.py
            self.buffer = []
            self.pending_data_to_send = False

        return self.recv_crypto.crypt(data)

    def _derive_crypto(self, pad_string): # XXX consider secret_seed
        """
        Derive and return an obfs2 key using the pad string in 'pad_string'.
        """
        secret = self.mac(pad_string,
                          self.initiator_seed + self.responder_seed,
                          self.shared_secret)
        return aes.AES_CTR_128(secret[:KEYLEN], secret[KEYLEN:],
                               counter_wraparound=True)

    def _derive_padding_crypto(self, seed, pad_string): # XXX consider secret_seed
        """
        Derive and return an obfs2 padding key using the pad string in 'pad_string'.
        """
        secret = self.mac(pad_string,
                          seed,
                          self.shared_secret)
        return aes.AES_CTR_128(secret[:KEYLEN], secret[KEYLEN:],
                               counter_wraparound=True)

    def mac(self, s, x, secret):
        """
        obfs2 regular MAC: MAC(s, x) = H(s | x | s)

        Optionally, if the client and server share a secret value SECRET,
        they can replace the MAC function with:
        MAC(s,x) = H^n(s | x | H(SECRET) | s)

        where n = HASH_ITERATIONS.
        """
        if secret:
            secret_hash = h(secret)
            return hn(s + x + secret_hash + s, self.ss_hash_iterations)
        else:
            return h(s + x + s)

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
                content = self.receivedDownstream(incomming_event.payload['content'])
            elif incomming_event.source_ID == self.dest_above:
                endpoint = self.dest_below
                content = self.receivedUpstream(incomming_event.payload['content'])
            else:
                raise Exception("Received event from unknown endpoint")

            if not content:
                return True

            payload = self.create_payload(content)
            outgoing_event = self.create_event(incomming_event.event_type, \
                                            endpoint, payload)
            
            #Gather information about sending each event
            ret = self.send_event(outgoing_event)
            rsp = rsp and ret

        #Evaluate if it is succesful
        if not rsp:
            raise Exception("Failed to process an event")
        return rsp

if __name__ == '__main__':
    pass