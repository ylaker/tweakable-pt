# Run the test through
# $ py.test ComponentTest.py 

import pytest

@pytest.mark.lib
def test_pytest_present():
    """
    Try to import pytest to ensure they are present and 
    accessible to python environment
    """
    import pytest
    assert True

@pytest.mark.lib
def test_code_present():
    """
    Try to import the code files
    """
    import tweakable_pt.EventQueue
    import tweakable_pt.components.Base
    assert True

@pytest.mark.component
def test_init_component():
    """
    Try to init a component
    """
    import sys
    import threading

    from tweakable_pt.EventQueue import EventQueue, Event
    from tweakable_pt.components.Base import BasicComponent
    
    #Create the condition
    condition = threading.Condition()
    
    #Create the queue and one event
    queue = EventQueue(condition)
    event = Event(1, 2, "data")

    #Create the component
    component = BasicComponent(2, 1, queue)

    #Start it
    component.start()

    #Add the event to the queue
    condition.acquire()
    queue.add(event)
    condition.notify_all()
    condition.release()

    #Wait for the component to process this event
    component.join()

    #Build the event expected as a result of this process
    out_event = Event(2, 1, "data")

    #Assert validity
    for event in queue.preview().values():
        assert event == out_event

@pytest.mark.component
def test_network_component_downstream():
    """
    Test to establish a tcp connection with a server, send content retrieved 
    from an event from the queue and add an event made from data from the network
    Run by "py.test ComponentTest.py", need to have "python ServerTest.py" 
    running in another terminal. 
    """
    import threading
    import time

    from twisted.internet import reactor

    import tweakable_pt.components.Networking.Downstream as Downstream

    from tweakable_pt.EventQueue import EventQueue, Event
    from tweakable_pt.components.Network import NetworkComponent

    #Create the condition
    condition = threading.Condition()

    #Create the queue and one event
    queue = EventQueue(condition)
    event = Event(1, 2, "data")
    content = "Downstream test"
    event.set_payload({'event_ID': 1, 'stream_ID': 1, 'timestamp': 1.0, \
                        'valid_for': 1, 'content': content})

    config = {\
                "name": "Downstream",\
                "ID": 2,\
                "module": "components.Network",\
                "class": "NetworkComponent",\
                "dest_above": 1,\
                "dest_below": -1,\
                "host": unicode("127.0.0.1"),\
                "port": 9151\
            }

    #Create the component
    component = NetworkComponent(config, "client", queue)

    down_fact = Downstream.DownstreamFactory(component)
    reactor.connectTCP('127.0.0.1', 28000, down_fact)

    #Start it
    component.start()

    #Add the event to the queue
    condition.acquire()
    queue.add(event)
    condition.notify_all()
    condition.release()

    #Stopping the reactor after 3 seconds, should be enough to send and receive.
    def stopping():
    	reactor.stop()
    reactor.callLater(3, stopping)

    reactor.run()
    
    #Wait for the component to process this event
    component.join()

    #Assert validity
    out_event = Event(2, 1, "data")
    out_event.set_payload({'event_ID': 1, 'stream_ID': 1, 'timestamp': 1.0, \
                        'valid_for': 1, 'content': "Received: "+content})

    for event in queue.preview().values():
        assert event == out_event

 
