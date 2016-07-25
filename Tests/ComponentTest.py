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
    import tweakable_pt.TweakableComponents.EventQueue
    import tweakable_pt.TweakableComponents.BaseComponent
    assert True

@pytest.mark.component
def test_init_component():
    """
    Try to init a component
    """
    import sys
    import threading

    from tweakable_pt.TweakableComponents.EventQueue import EventQueue, Event
    from tweakable_pt.TweakableComponents.BaseComponent import BasicComponent

    #Create the queue and one event
    queue = EventQueue()
    event = Event(1, 2, "data")

    #Create the condition
    condition = threading.Condition()

    #Create the component
    component = BasicComponent(2, queue, 1, condition)

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
    out_event.set_payload("payload")

    #Assert validity
    for event in queue.preview().values():
        assert event == out_event

@pytest.mark.component
def test_network_component():
    import threading
    import time

    from twisted.internet import reactor

    import tweakable_pt.Connectivity.Downstream as Downstream

    from tweakable_pt.TweakableComponents.EventQueue import EventQueue, Event
    from tweakable_pt.TweakableComponents.NetworkComponent import NetworkComponent

    #Create the queue and one event
    queue = EventQueue()
    event = Event(1, 2, "data")

    #Create the condition
    condition = threading.Condition()

    #Create the component
    component = NetworkComponent(2, queue, 1, condition)

    down_fact = Downstream.DownstreamFactory(component)
    reactor.connectTCP('127.0.0.1', 28000, down_fact)

    #Start it
    component.start()

    #Add the event to the queue
    condition.acquire()
    queue.add(event)
    condition.notify_all()
    condition.release()

    
    #reactor.run()
    #Wait for the component to process this event
    component.join()

    print str(queue)

    assert False





