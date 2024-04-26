# goose (🪿)

Matching Engine for Passenger-to-Driver matching at RideNow

# Tools and Libraries

## Core Tooling
* Orchestration: [Docker Compose](https://docs.docker.com/compose/)
* Containerization: [Docker](https://docs.docker.com/manuals/)
* Static Code Analysis: [CodeClimate](https://codeclimate.com/quality)

## Core libraries
* **asyncio**: async runtime
* **redis-py**: python redis toolkit
* **pymongo**: mongodb driver for python
* **loguru**: logging rotation, retention and compression

# Docker build commands

```bash
# build docker image
docker build -t fredebode/goose .

# run docker image locally
docker run -d --name goose -p 80:80 fredebode/goose:latest
```

## GeoLocation Requests
A successful GET method typically returns HTTP status code 200 (OK). If the resource cannot be found, the method should return 404 (Not Found).

If the request was fulfilled but there is no response body included in the HTTP response, then it should return HTTP status code 204 (No Content); for example, a search operation yielding no matches might be implemented with this behavior.

## Match-making request
If a POST method creates a new resource, it returns HTTP status code 201 (Created). The URI of the new resource is included in the Location header of the response. The response body contains a representation of the resource.