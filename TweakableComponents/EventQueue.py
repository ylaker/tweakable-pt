#Connection manager used to link and relay data between upstream and 
#downstream connections.
class ConnectionManager():
    def __init__(self):
        self.downstream_conn = None
        self.upstream_conn = None

    def set_upstream_conn(self, conn):
        self.upstream_conn = conn

    def set_downstream_conn(self, conn):
        self.downstream_conn = conn

    def is_ready(self):
        return self.downstream_conn and self.upstream_conn

#Class defining the events
class Event:
    def __init__(self, source_ID, dest_ID, event_type):
        #Assert validity of the parameters received
        if not isinstance(source_ID, int) or \
                not isinstance(dest_ID, int) or \
                not (event_type == "data" or event_type == "control"):
            raise Exception("Malformed input")

        #Add attributes to the event
        self.source_ID = source_ID
        self.dest_ID = dest_ID
        self.event_type = event_type
        self.payload = {}

    def set_payload(self, payload):
        #Assert validity of the parameter received
        if not (isinstance(payload, dict) or payload == 'payload'):
            raise Exception("Malformed input payload")

        if not payload == 'payload':
            if self.event_type == "control":
                if not len(payload) == 2 or \
                        not (payload['dest_location'] == "local" or  \
                                payload['dest_location'] == "remote") or \
                        not isinstance(payload['configuration'], dict):
                    raise Exception("Malformed input payload")

            if self.event_type == "data":
                if not len(payload) == 5 or \
                        not isinstance(payload['event_ID'], int) or \
                        not isinstance(payload['stream_ID'], int) or \
                        not isinstance(payload['timestamp'], float) or \
                        not isinstance(payload['valid_for'], int) or \
                        not isinstance(payload['content'], str):
                    raise Exception("Malformed input payload")

        #Add payload to the event
        self.payload = payload

    def __str__(self):
        rsp = "{source_ID : %s, dest_ID : %s, event_type: %s, payload: %s}" \
                % (self.source_ID, self.dest_ID, self.event_type, self.payload)
        return rsp

    def __repr__(self):
        return str(self)

    def __eq__(self, other): 
        return self.__dict__ == other.__dict__

#Class defining the queue
class EventQueue:
    def __init__(self, add_event_condition):
        self.queue = {}
        self.index = 0
        self.condition = add_event_condition

    #Method removing and returning an event from the queue
    def get(self, ID, index):
        event = self.queue[index]
        if event.dest_ID != ID:
            raise Exception("ID does not match destination ID")
        del self.queue[index]
        return event

    #Method returning an event without removing it from the queue
    def peek(self, index):
        event = self.queue[index]
        return event

    #Method to add an event to the queue
    def add(self, event):
        self.index = self.index + 1
        self.queue[self.index] = event
        return True

    #Method to test whether the queue is empty
    def is_empty(self):
        empty = False
        if not self.queue:
            empty = True
        return empty

    #Method to return the queue 
    def preview(self):
        rsp = {}
        for key, value in self.queue.items():
            rsp[key] = value
        return rsp

    def __str__(self):
        rsp = "%s" % (self.queue)
        return rsp

#To be sure nothing happen when importing this file or executing it
if __name__ == '__main__':
    pass
