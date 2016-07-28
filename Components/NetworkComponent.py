import logging
import threading

from twisted.internet import reactor, protocol

import Network.Downstream as Downstream
import Network.Upstream as Upstream

from BaseComponent import BasicComponent


class NetworkComponent(BasicComponent):
    """
    Network component. Its role is to manage a connection 
    and push data received from the network to the queue wrapped as an event. 
    Used by both upstream and downstream connections to interface with the queue.
    """
    def __init__(self, config, mode, queue):
        if not (config['name'] == "Upstream" or config['name'] == "Downstream") or \
                not isinstance(config['host'], unicode) or \
                not isinstance(config['port'], int):
            raise Exception("Malformed config")

        self.connection = None
        self.conn_condition = threading.Condition()
        self.host = config['host']
        self.port = config['port']

        dest_endpoint = (config['dest_above'], config['dest_below'])

        BasicComponent.__init__(self, config['ID'], dest_endpoint, mode, queue)

        if config['name'] == "Upstream":
            self.setup_upstream()
        else:
            self.setup_downstream()
        
    def setup_upstream(self):
        if self.mode == "client":
            try:
                up_fact = Upstream.UpstreamClientFactory(self)
                reactor.listenTCP(self.port, up_fact, interface = self.host)
            except Exception, e:
                logging.warning("UpstreamInit: %s" %e)

        if self.mode == "server":
            try:
                up_fact = Upstream.UpstreamServerFactory(self)
                reactor.connectTCP(self.host, self.port, up_fact)
            except Exception, e:
                logging.warning("Upstream: %s" %e)

    def setup_downstream(self):
        if self.mode == "client":
            try:
                down_fact = Downstream.DownstreamFactory(self)
                reactor.connectTCP(self.host, self.port, down_fact)
            except Exception, e:
                logging.warning("DownstreamInit: %s" %e)

        if self.mode == "server":
            try:
                down_fact = Downstream.DownstreamFactory(self)
                addrport = reactor.listenTCP(self.port, down_fact, interface = self.host)
            except Exception, e:
                logging.warning("Downstream: %s" % e)


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

    #Method used to create the thread for a component
    def run(self):
        while True:
            self.condition.acquire()
            #Loop until it get events related to its component ID
            while self.get_events():
                #Wait to receive a notification for a change in the queue
                self.condition.wait()
            #Events received, processing
            try:
                self.process_events()
            except Exception as e:
                logging.warning(str(e))
            #Release the underlying lock
            self.condition.release()

if __name__ == '__main__':
    pass