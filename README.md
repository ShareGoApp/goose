# goose (🪿)

Matching Engine for Passenger-to-Driver matching at RideNow

- guide (docker)  : https://fastapi.tiangolo.com/deployment/docker/
- guide (motor)   : https://motor.readthedocs.io/en/stable/tutorial-asyncio.html
- guide (rest)    : https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design

# Docker build commands

```bash
# build docker image
docker build -t fredebode/goose .

# run docker image locally
docker run -d --name goose -p 80:80 fredebode/goose:latest
```

```bash
# build docker image
docker build -t fredebode/goose .

# push docker image to dockerhub
docker push
```

# Libraries

* **Loguru**: terminal logger w. easier file logging with rotation / retention / compression
* **asyncio**: async runtime
* **redis**:
* **pymongo**: low-level mongodb driver, to perfrom NoSQL operations


## GET methods
A successful GET method typically returns HTTP status code 200 (OK). If the resource cannot be found, the method should return 404 (Not Found).

If the request was fulfilled but there is no response body included in the HTTP response, then it should return HTTP status code 204 (No Content); for example, a search operation yielding no matches might be implemented with this behavior.

## POST methods
If a POST method creates a new resource, it returns HTTP status code 201 (Created). The URI of the new resource is included in the Location header of the response. The response body contains a representation of the resource.