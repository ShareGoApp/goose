# goose (🪿)

Matching Engine for Passenger-to-Driver matching at RideNow

# Tools and Libraries

## Core Tooling

- Orchestration: [Docker Compose](https://docs.docker.com/compose/)
- Containerization: [Docker](https://docs.docker.com/manuals/)
- Static Code Analysis: [CodeClimate](https://codeclimate.com/quality)

## Core libraries

- **asyncio**: async runtime
- **redis-py**: python redis toolkit
- **pymongo**: mongodb driver for python
- **loguru**: logging rotation, retention and compression

## Running the service

```bash
# starts the service with development settigns
python app/main.py
```

```bash
# starts the service with production settigns
python app/main.py prod
```

## Docker build commands

```bash
# build docker image
docker build -t fredebode/goose .

# run docker image locally
docker run -d --name goose -p 80:80 fredebode/goose:latest
```

## geo-lookup event

this service handles geo-lookup events ...

```json
geo_request:{"passenger_id": id, "max_radius": 500}
```

## match-making event

this service handles match-making events ...

```json
mat_request:{"passenger_id": id, "driver_ids": [...ids]}
```

## match-save event

this service handles match-save events ...

```json
sav_request:{"passenger_id": pid, "driver_id": did, "min_err": <computed_err>}
```
