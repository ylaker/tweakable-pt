import logging

from threading import Thread

class BasicComponent(Thread):
    """
    Basic class, more elaborated components will herit from this class.
    """
    def __init__(self, ID, dest_endpoint, mode, queue):
        #Assert validity of the parameters received
        endpoint_above, endpoint_below = dest_endpoint

        if not (mode == "server" or mode == "client"):
            raise Exception("Malformed input")

        if not isinstance(ID, int) or \
                not isinstance(endpoint_below, int) or \
                not isinstance(endpoint_above, int):
            raise Exception("Malformed input")

        self.queue = queue
        self.dest_above = endpoint_above
        self.dest_below = endpoint_below
        self.ID = ID
        self.mode = mode
        self.incomming_events = {}
        self.condition = queue.condition

        #Init the parent class
        Thread.__init__(self)

    def create_payload(self, content):
        payload = {}
        payload['event_ID'] = 1
        payload['stream_ID'] = 1
        payload['timestamp'] = 1.0
        payload['valid_for'] = 1
        payload['content'] = content

        return payload

    #Method to create an event
    def create_event(self, event_type, endpoint, payload = "payload"):
        if not (endpoint == self.dest_above or endpoint == self.dest_below):
            raise Exception("Malformed input")
        try:
            event = self.queue.create_event(self.ID, endpoint, event_type)
            event.set_payload(payload)
        except Exception as e:
            logging.error(str(e))

        return event

    #Method to send an event to the queue
    def send_event(self, event):
        self.condition.acquire()
        rsp = self.queue.add(event)
        self.condition.notify_all()
        self.condition.release()
        return rsp

    #Method to process an event retrieved from the queue, 
    #Must me implemented in child class
    def process_events(self):
        pass

    #Method to get events, depends on what this component do (peek, get or ...)
    def get_events(self):
        empty = True
        prev = self.queue.preview()
        for key, value in prev.items():
            if value.dest_ID == self.ID:
                self.incomming_events[key] = self.queue.get(self.ID, key)
                empty = False
        return empty

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