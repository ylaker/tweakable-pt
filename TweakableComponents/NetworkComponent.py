import logging
import threading

from BaseComponent import BasicComponent


class NetworkComponent(BasicComponent):
    """
    Network component. Its role is to manage a connection 
    and push data received from the network to the queue wrapped as an event. 
    Used by both upstream and downstream connections to interface with the queue.
    """
    def __init__(self, ID, dest_endpoint, queue, condition):
        self.connection = None
        self.conn_condition = threading.Condition()
        BasicComponent.__init__(self, ID, dest_endpoint, queue, condition)

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

        #Create the event
        event = self.create_event(payload)
        #Sending the event
        self.send_event(event)

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
            incomming_payload = self.incomming_events[key].payload
            #Process details from the payload (not implemented yet)
            #Retrieve the outgoing data
            outgoing_data = incomming_payload['content']
            #Send the content towards the network
            self.connection.transport.write(outgoing_data)

        return True

if __name__ == '__main__':
    pass