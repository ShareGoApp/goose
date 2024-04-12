# goose
🪿 Ride Matching Engine

- guide (docker)  : https://fastapi.tiangolo.com/deployment/docker/
- guide (motor)   : https://motor.readthedocs.io/en/stable/tutorial-asyncio.html
- guide (rest)    : https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design

# Docker build commands
- Build Image: docker build -t reports-service .
- Run container: docker run -d --name reports_container -p 80:80 reports-service

# Api Design
- /reports
    - POST: post new report
    - GET: retrieve all reports (list)
    - PUT: Bulk update of reports
    - DELETE: delete all reports (should not be included)
- /reports/:id
    - POST: Error
    - GET: Retrieve the details for report:id (detail)
    - PUT: Update the details of report:id (if exists)
    - DELETE: remove report:id (if exists)


## GET methods
A successful GET method typically returns HTTP status code 200 (OK). If the resource cannot be found, the method should return 404 (Not Found).

If the request was fulfilled but there is no response body included in the HTTP response, then it should return HTTP status code 204 (No Content); for example, a search operation yielding no matches might be implemented with this behavior.

## POST methods
If a POST method creates a new resource, it returns HTTP status code 201 (Created). The URI of the new resource is included in the Location header of the response. The response body contains a representation of the resource.

If the method does some processing but does not create a new resource, the method can return HTTP status code 200 and include the result of the operation in the response body. Alternatively, if there is no result to return, the method can return HTTP status code 204 (No Content) with no response body.

If the client puts invalid data into the request, the server should return HTTP status code 400 (Bad Request). The response body can contain additional information about the error or a link to a URI that provides more details.

## PUT methods
If a PUT method creates a new resource, it returns HTTP status code 201 (Created), as with a POST method. If the method updates an existing resource, it returns either 200 (OK) or 204 (No Content). In some cases, it might not be possible to update an existing resource. In that case, consider returning HTTP status code 409 (Conflict).

Consider implementing bulk HTTP PUT operations that can batch updates to multiple resources in a collection. The PUT request should specify the URI of the collection, and the request body should specify the details of the resources to be modified. This approach can help to reduce chattiness and improve performance.

## DELETE methods
If the delete operation is successful, the web server should respond with HTTP status code 204 (No Content), indicating that the process has been successfully handled, but that the response body contains no further information. If the resource doesn't exist, the web server can return HTTP 404 (Not Found).