import requests
import paho.mqtt.client as mqtt
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import time


api_url = 'https://api.entur.io/realtime/v1/rest/et?datasetId=RUT'
stop_point_ref = 'NSR:Quay:12345' # Replace with your desired StopPointRef

# MQTT details
mqtt_broker = 'mqtt.example.com'  # Replace with your MQTT broker address
mqtt_port = 1883    # Replace with your MQTT broker port
mqtt_topic = '/entur/' + stop_point_ref # Replace with your desired MQTT topic

# Function to check if XML data is complete
def is_xml_data_complete(xml_data):
    try:
        root = ET.fromstring(xml_data)
        ns = {
            'siri': 'http://www.siri.org.uk/siri',
            'ns2': 'http://www.ifopt.org.uk/acsb',
            'ns3': 'http://www.ifopt.org.uk/ifopt',
            'ns4': 'http://datex2.eu/schema/2_0RC1/2_0'
        }
        # Check if there are any EstimatedVehicleJourney elements in the XML
        estimated_journeys = root.findall('.//siri:EstimatedVehicleJourney', ns)
        return len(estimated_journeys) > 0
    except ET.ParseError:
        return False

# Function to retrieve data from API
def get_api_data(api_url):
    
    response = requests.get(api_url)
    data = response.text
    return data

# Function to publish data to MQTT
def publish_to_mqtt(broker, port, topic, data):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(broker, port)
    client.publish(topic, data)
    client.disconnect()


# Function to extract data for a specific StopPointRef from XML
def extract_data_for_stop_point(xml_data, stop_point_ref):
    root = ET.fromstring(xml_data)
    ns = {
        'siri': 'http://www.siri.org.uk/siri',
        'ns2': 'http://www.ifopt.org.uk/acsb',
        'ns3': 'http://www.ifopt.org.uk/ifopt',
        'ns4': 'http://datex2.eu/schema/2_0RC1/2_0'
    }
    data = []
    for estimated_journey in root.findall('.//siri:EstimatedVehicleJourney', ns):
        for recorded_call in estimated_journey.findall('.//siri:EstimatedCall', ns):
            stop_point = recorded_call.find('siri:StopPointRef', ns)
            if stop_point is not None and stop_point.text == stop_point_ref:
                expected_arrival_time_str = recorded_call.find('siri:ExpectedArrivalTime', ns).text if recorded_call.find('siri:ExpectedArrivalTime', ns) is not None else recorded_call.find('siri:AimedArrivalTime', ns).text
                expected_arrival_time = datetime.fromisoformat(expected_arrival_time_str.replace('Z', '+00:00'))
                minutes_to_arrival = int((expected_arrival_time - datetime.now(timezone.utc)).total_seconds() / 60)
                
                call_data = {
                    'StopPointRef': stop_point.text,
                    'Order': recorded_call.find('siri:Order', ns).text,
                    'StopPointName': recorded_call.find('siri:StopPointName', ns).text,
                    'AimedArrivalTime': recorded_call.find('siri:AimedArrivalTime', ns).text,
                    'ExpectedArrivalTime': recorded_call.find('siri:ExpectedArrivalTime', ns).text if recorded_call.find('siri:ExpectedArrivalTime', ns) is not None else None,
                    'AimedDepartureTime': recorded_call.find('siri:AimedDepartureTime', ns).text,
                    'VehicleRef': estimated_journey.find('siri:VehicleRef', ns).text if estimated_journey.find('siri:VehicleRef', ns) is not None else None,
                    'DestinationDisplay': recorded_call.find('siri:DestinationDisplay', ns).text if recorded_call.find('siri:DestinationDisplay', ns) is not None else None,
                    'MinutesToArrival': minutes_to_arrival
                }
                data.append(call_data)
    return data

def convert_zeros_to_dash(input_string):
    # Use regular expression to replace one or more zeros with a single dash
    output_string = re.sub(r'00+', '-', input_string)
    return output_string



# Main script
if __name__ == '__main__':
    while True:
        # Get current timestamp and date
        current_timestamp = datetime.now()
        current_date = datetime.now().date().isoformat()
    
        # Publish timestamp and date to MQTT
        publish_to_mqtt(mqtt_broker, mqtt_port, mqtt_topic + "/time",current_timestamp.strftime('%H:%M:%S'))
        publish_to_mqtt(mqtt_broker, mqtt_port,mqtt_topic + "/date",current_date)
        
        #data = get_api_data(api_url)
        while True:
            data = get_api_data(api_url)
            if is_xml_data_complete(data):
                break
            time.sleep(2)  # Wait for 2 seconds before retrying


    # Extract data for NSR:Quay:11870
        extracted_data = extract_data_for_stop_point(data, stop_point_ref)

        # Order the extracted data by AimedArrivalTime
        ordered_data = sorted(extracted_data, key=lambda x: x['AimedArrivalTime'])
        
        # Print the extracted data
        entry_counter = 0
        for entry in ordered_data:
            publish_to_mqtt(mqtt_broker, mqtt_port, mqtt_topic + "/json" + str(entry_counter), str(entry))
            publish_to_mqtt(mqtt_broker, mqtt_port, mqtt_topic + "/vehicle" + str(entry_counter), convert_zeros_to_dash(entry['VehicleRef']))
            publish_to_mqtt(mqtt_broker, mqtt_port, mqtt_topic + "/Destination" + str(entry_counter), entry['DestinationDisplay'])
            if entry['MinutesToArrival'] == 0:
                publish_to_mqtt(mqtt_broker, mqtt_port, mqtt_topic + "/departsIn" + str(entry_counter), "Nå")
            else:
                publish_to_mqtt(mqtt_broker, mqtt_port, mqtt_topic + "/departsIn" + str(entry_counter), entry['MinutesToArrival'])
            print(entry)
            entry_counter += 1
        time.sleep(15)

