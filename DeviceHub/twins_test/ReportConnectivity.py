import time
import iothub_client
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult, IoTHubError

CONNECTION_STRING = "HostName=bobul.azure-devices.net;DeviceId=sogkit;SharedAccessKey=K7jMiwT30e/jMgeD9vH9EEwIn0c07/zeg0HxBcmjQB4="

# choose HTTP, AMQP, AMQP_WS or MQTT as transport protocol
PROTOCOL = IoTHubTransportProvider.MQTT

TIMER_COUNT = 5
TWIN_CONTEXT = 0
SEND_REPORTED_STATE_CONTEXT = 0

def device_twin_callback(update_state, payload, user_context):
    print ( "" )
    print ( "Twin callback called with:" )
    print ( "    updateStatus: %s" % update_state )
    print ( "    payload: %s" % payload )

def send_reported_state_callback(status_code, user_context):
    print ( "" )
    print ( "Confirmation for reported state called with:" )
    print ( "    status_code: %d" % status_code )

def iothub_client_init():
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)

    if client.protocol == IoTHubTransportProvider.MQTT or client.protocol == IoTHubTransportProvider.MQTT_WS:
        client.set_device_twin_callback(
            device_twin_callback, TWIN_CONTEXT)

    return client

def iothub_client_sample_run():
    try:
        client = iothub_client_init()

        if client.protocol == IoTHubTransportProvider.MQTT:
            print ( "Sending data as reported property..." )

            reported_state = "{\"connectivity\":\"cellular\"}"

            client.send_reported_state(reported_state, len(reported_state), send_reported_state_callback, SEND_REPORTED_STATE_CONTEXT)

        while True:
            print ( "Press Ctrl-C to exit" )

            status_counter = 0
            while status_counter <= TIMER_COUNT:
                status = client.get_send_status()
                time.sleep(10)
                status_counter += 1 
    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )
        
if __name__ == '__main__':
    print ( "Starting the IoT Hub Device Twins Python client sample..." )

    iothub_client_sample_run()
