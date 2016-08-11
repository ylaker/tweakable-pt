import logging
import sys
import traceback

from Base import BasicComponent

from Bananaphone.BananaphoneMethods import rh_build_encoder_factory, rh_decoder

class BananaphoneComponent(BasicComponent):
    """
    BananaphoneComponent implements the Bananaphone protocol
    """
    def __init__(self, config, mode, queue):
        if not isinstance(config['config'], dict):
            raise Exception("Bananaphone: Malformed config")

        dest_endpoint = (config['dest_above'], config['dest_below'])

        BasicComponent.__init__(self, config['ID'], dest_endpoint, mode, queue)

        self.gatherer = ""

        if mode == "client":
            self.initiator = True
        else:
            self.initiator = False

        try:
            self.setup(config['config'])
        except Exception, e:
            logging.error("Bananaphone: %s" % e)
        

    def setup(self, config):
        """
        Setup server for the obfs2 protocol.
        The client and server differ in terms of their padding strings.
        """
        if not len(config) == 4 or\
                not 'modelName' in config or\
                not 'encodingSpec' in config or\
                not 'corpus' in config or\
                not 'order' in config:
            raise Exception("Bananaphone: Malformed setup config")

        abridged = None
        modelName = config['modelName']
        corpus = config['corpus']
        order = config['order']
        encodingSpec = config['encodingSpec']

        if modelName == 'markov':
            args = [ corpus, order, abridged ]
        elif modelName == 'random':
            args = [ corpus ]
        else:
            logging.error("BananaphoneTransport: unsupported model type")
            return

        # expensive model building operation
        logging.warning("Bananaphone: building encoder %s model" % modelName)
        encoder_factory = rh_build_encoder_factory(encodingSpec, modelName, *args)
        decoder_factory = lambda: rh_decoder(encodingSpec)

        self.encode = encoder_factory()
        self.decode = decoder_factory()

        self.encoder = self.encode > self.gathering_data
        self.decoder = self.decode > self.gathering_data

    def gathering_data(self, content):
        self.gatherer += content

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
                try:
                    self.decoder.send(incomming_event.payload['content'])
                except Exception, e:
                    logging.warning("Bananaphone: %s" % e)
                    logging.exception("Exception")
            elif incomming_event.source_ID == self.dest_above:
                endpoint = self.dest_below
                try:
                    self.encoder.send(incomming_event.payload['content'])
                except Exception, e:
                    logging.warning("Bananaphone: %s" % e)
                    logging.exception("Exception")
            else:
                raise Exception("Received event from unknown endpoint")

            content = self.gatherer
            self.gatherer = ""
            payload = self.create_payload(content)
            outgoing_event = self.create_event(incomming_event.event_type, \
                                            endpoint, payload)
            
            #Gather information about sending each event
            self.send_event(outgoing_event)


        return rsp

if __name__ == '__main__':
    pass