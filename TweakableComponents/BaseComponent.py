import logging

from threading import Thread

from EventQueue import Event, EventQueue

class BasicComponent(Thread):
    """
    Basic class, more elaborated components will herit from this class.
    """
    def __init__(self, ID, dest_endpoint, queue):
        #Assert validity of the parameters received
        if not isinstance(ID, int) or \
                not isinstance(dest_endpoint, int) or \
                not isinstance(queue, EventQueue):
            raise Exception("Malformed input")

        self.queue = queue
        self.dest_endpoint = dest_endpoint
        self.ID = ID
        self.incomming_events = {}
        self.condition = queue.condition

        #Init the parent class
        Thread.__init__(self)

    #Method to create an event
    def create_event(self, payload = "payload"):
        try:
            event = Event(self.ID, self.dest_endpoint, "data")
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

    #Method to process an event retrieved from the queue
    def process_events(self):
        rsp = True
        for key in sorted(self.incomming_events):
            #Process each event 
            incomming_payload = self.incomming_events[key].payload
            outgoing_event = self.create_event(incomming_payload)
            
            #Gather information about sending each event
            ret = self.send_event(outgoing_event)
            rsp = rsp and ret

        #Evaluate if it is succesful
        if not rsp:
            raise Exception("Failed to process an event")
        return rsp

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
                #logging.error(str(e.value))
            #Release the underlying lock
            self.condition.release()

if __name__ == '__main__':
    pass