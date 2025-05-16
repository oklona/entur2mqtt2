# Entur2MQTT - version 2

I already had an Entur2MQTT, based on php. Entur made some changes to their APIs in 2024 some time, where it is no longer possible to only retrieve data from one specific quay. You basically need to receive the entire dataset in XML from Entur. For my own part, I fixed this by making a "hack", converting parts of the XML document to a table in PHP, and then fetching data based on where in the XML table I would find the data.

However, my hack didn't work too well, as I didn't take into account that the ExpectedArrival parameter was not in the XML document for departures that were on time, and weren't expected for a few minutes.

So, I decided to rewrite the entire thing, using Python, which seems to be a more popular language now. -And here is the result. I do return more values than in the previous version, and I also return JSON of the entire datasets.

Additional info you should configure:

- Quay or StopID to retrieve data from This can be found by visiting https://stoppested.entur.org (login guest/guest), and find either a quay ID, or a StopPlace ID. The difference between "quay" and "stopplace" is that the quay is a specific platform, in a specific direction for the stopplace. A stopplace can also encapsulate several other stopplaces in places where there are several different services in a limited geographic area.
- Text to use for "Now". When time to departure is "0", most public screens show the Norwegian word "Nå", meaning "Now". Here, you can choose which word to return for this specific use case.
- Mosquitto host
- Mosquitto username and password
- Base topic to use when publishing Mosquitto data. The quay/stopplace ID will be added to the base topic, to make it easier to distinguish, in case you run multiple instances of the script to retrieve data from more than one stop place.

All of these can be set directly in the top of the script, or by specifying environment variables:

- STOP_POINT_REF
- NOW_WORD
- MQTT_BROKER
- MQTT_PORT
- MQTT_USERNAME
- MQTT_PASSWORD
- MQTT_TOPIC


## Docker
I run all my <API>2mqtt instances in Docker, to simplify deployment. 
To run in Docker, use the (very simple) included Dockerfile and build the image by running a command like:

```
docker build -t entur2mqtt .
```

You can then create and run the container by issuing the following (example environment variables added, the ones listed above may be used in addition to TZ):

```
docker run -d -e TZ=<TimeZone> -e STOP_POINT_REF="NSR:Quay:54321" -e MQTT_BROKER=<mqtt-broker> -e MQTT_PORT=<mqtt_port> --name entur2mqtt --restart always entur2mqtt:latest
```
