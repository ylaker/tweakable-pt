# Run the test through
# $ py.test QueueTest.py 

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
    import Queue
    import Threads
    assert True

@pytest.mark.event
def test_create_event():
    """
    Test the creation of an event
    """
    from Queue import Event

    event = Event(1, 2, "control")

    assert event.source_ID == 1
    assert event.dest_ID == 2
    assert event.event_type == "control"
    assert event.payload == {}

@pytest.mark.event
def test_fail_create_event():
    """
    Test the exception raising when the input is malformed
    """
    from pytest import raises
    from Queue import Event

    with raises(Exception) as excinfo:
        event = Event(1, 2, "error")
    assert "Malformed input" in str(excinfo.value)

    with raises(Exception) as excinfo:
        event = Event(1, "error", "control")
    assert "Malformed input" in str(excinfo.value)

    with raises(Exception) as excinfo:
        event = Event("error", 2, "data")
    assert "Malformed input" in str(excinfo.value)

@pytest.mark.event
def test_set_payload():
    """
    Test to set the payload for data and control event
    """
    from Queue import Event

    data_event = Event(1, 2, "data")
    control_event = Event(1, 2, "control")

    data_payload = {'event_ID': 1, \
                    'stream_ID': 1, \
                    'timestamp': 1.0, \
                    'valid_for': 2, \
                    'content': {}}
    control_payload =  {'dest_location': "local", \
                        'configuration': {}}

    data_event.set_payload(data_payload)

    assert data_event.payload == data_payload

    control_event.set_payload(control_payload)

    assert control_event.payload == control_payload

@pytest.mark.event
def test_fail_set_payload():
    """
    Test cases where exception should be thrown by the
    set_payload method from Event
    """
    from pytest import raises
    from Queue import Event

    data_event = Event(1, 2, "data")
    control_event = Event(1, 2, "control")

    #Test fail cases of payload for data event
    with raises(Exception) as excinfo:
        data_event.set_payload({'event_ID': "error", \
                                'stream_ID': 1, \
                                'timestamp': 1.0, \
                                'valid_for': 2, \
                                'content': {}})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        data_event.set_payload({'event_ID': 1, \
                                'stream_ID': "error", \
                                'timestamp': 1.0, \
                                'valid_for': 2, \
                                'content': {}})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        data_event.set_payload({'event_ID': 1, \
                                'stream_ID': 1, \
                                'timestamp': "error", \
                                'valid_for': 2, \
                                'content': {}})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        data_event.set_payload({'event_ID': 1, \
                                'stream_ID': 1, \
                                'timestamp': 1.0, \
                                'valid_for': "error", \
                                'content': {}})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        data_event.set_payload({'event_ID': 1, \
                                'stream_ID': 1, \
                                'timestamp': 1.0, \
                                'valid_for': 2, \
                                'content': "error"})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        data_event.set_payload({'event_ID': 1, \
                                'stream_ID': 1, \
                                'timestamp': 1.0, \
                                'valid_for': 2, \
                                'content': {}, \
                                'error': "error"})
    assert "Malformed input payload" in str(excinfo.value)

    #Test fail cases of payload for control event
    with raises(Exception) as excinfo:
        control_event.set_payload({'dest_location': "error", \
                                    'configuration': {}})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        control_event.set_payload({'dest_location': "local", \
                                    'configuration': "error"})
    assert "Malformed input payload" in str(excinfo.value)

    with raises(Exception) as excinfo:
        control_event.set_payload({'dest_location': "local", \
                                    'configuration': {}, \
                                    'error': "error"})
    assert "Malformed input payload" in str(excinfo.value)

@pytest.mark.queue
def test_add_queue():
    """
    Test adding an event to the queue
    """
    from Queue import EventQueue, Event

    q = EventQueue()
    event = Event(1, 2, "data")

    ans = q.add(event)

    assert q.queue == {1: event}
    assert ans == "Event added"

@pytest.mark.queue
def test_get_queue():
    """
    Tests the retrieval of an event from the queue
    """
    from Queue import EventQueue, Event

    q = EventQueue()

    event1 = Event(1, 2, "data")
    event2 = Event(1, 3, "control")

    q.add(event1)
    q.add(event2)

    rsp = q.get(2)
    
    assert q.queue == {1: event1}
    assert rsp == event2

@pytest.mark.queue
def test_peek_queue():
    """
    Tests the peek method of the queue which return 
    an event without removing it from the queue
    """
    from Queue import EventQueue, Event

    q = EventQueue()

    event1 = Event(1, 2, "data")
    event2 = Event(1, 3, "control")

    q.add(event1)
    q.add(event2)

    rsp = q.peek(2)
    
    assert q.queue ==  {1: event1, 2: event2}
    assert rsp == event2

@pytest.mark.queue
def test_preview_queue():
    """
    Tests the preview method which hide the payload and return
    the queue with payloads replaced by "payload"
    """
    from Queue import EventQueue, Event

    q = EventQueue()

    event1 = Event(1, 2, "data")
    event2 = Event(1, 3, "control")

    q.add(event1)
    q.add(event2)
    event1.payload = "payload"
    event2.payload = "payload"

    rsp = q.preview()

    assert rsp == {1: event1, 2: event2}
    