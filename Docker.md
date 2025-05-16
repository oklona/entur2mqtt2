#Docker

To run in Docker, use this simple Dockerfile and build the image by running a command like:

```
docker build -t entur2mqtt .
```

You can then create and run the container by issuing the following:

```
docker run -d -e TZ=$TZ --name entur2mqtt --restart always entur2mqtt:latest
```

