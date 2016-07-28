import logging
import threading

from BaseComponent import BasicComponent

class DummyComponent(BasicComponent):
    """
    Dummy component. Do nothing, just relay events.
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