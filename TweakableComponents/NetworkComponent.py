import logging
import threading

from BaseComponent import BasicComponent


class NetworkComponent(BasicComponent):
    """
    Network component. Its role is to manage a connection 
    and push data received from the network to the queue wrapped as an event. 
    Used by both upstream and downstream connections to interface with the queue.
    """
    def __init__(self, ID, dest_endpoint, queue):
        self.connection = None
        self.conn_condition = threading.Condition()

        BasicComponent.__init__(self, ID, dest_endpoint, queue)

    def data_from_connection(self, data):
        """
        Transform data into payload and send an event to the queue
        """
        payload = {}
        payload['event_ID'] = 1
        payload['stream_ID'] = 1
        payload['timestamp'] = 1.0
        payload['valid_for'] = 1
        payload['content'] = data

        if self.dest_above != -1:
            endpoint = self.dest_above
        elif self.dest_below != -1:
            endpoint = self.dest_below
        else:
            raise Exception("No valid endpoint")

        #Create the event
        try:
            event = self.create_event("data", endpoint, payload)
            #Sending the event
            self.send_event(event)
        except Exception as e:
            logging.error(str(e))
            
        return True

    def process_events(self):
        """
        Process events arriving from the queue
        """
        
        self.conn_condition.acquire()
        if not self.connection:
        	self.conn_condition.wait()
        self.conn_condition.release()

        for key in sorted(self.incomming_events):
            #Retrieve the content from the event 
            incomming_event = self.incomming_events.pop(key)
            #Process details from the payload (not implemented yet)
            #Retrieve the outgoing data
            outgoing_data = incomming_event.payload['content']
            #Send the content towards the network
            self.connection.transport.write(outgoing_data)

        return True

if __name__ == '__main__':
    pass