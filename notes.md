

## Use of Loguru

```python
# available logging commands
logger.trace("Executing program")
logger.debug("Processing data...")
logger.info("Server started successfully.")
logger.success("Data processing completed successfully.")
logger.warning("Invalid configuration detected.")
logger.error("Failed to connect to the database.")
logger.critical("Unexpected system error occurred. Shutting down.")
```


## GeoSpatial Queries (MongoDB)

*  [link](https://www.mongodb.com/docs/manual/tutorial/geospatial-tutorial/)


# sample requests

1. geo_request:{"passenger_id": "661fc362bc83e7536732d787", "max_radius": 500}
2. mat_request:{"passenger_id": "661fc362bc83e7536732d787", "driver_ids": ["661fc59bbc83e7536732d788", "661fc5c0bc83e7536732d789"]}
3. sav_request:{"passenger_id": "661fc362bc83e7536732d787", "driver_id": "661fc59bbc83e7536732d788", "min_err": 0.0002828427124789841}