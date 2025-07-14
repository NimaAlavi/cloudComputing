## Building and Running the Docker Image

1. Build the Docker image:
   ```bash
   docker build -t my-http-server .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 my-http-server
   ```
   The server will be available at `http://localhost:8000`.

## Testing the Server

- **GET Request**: Retrieve the current status.
  ```bash
  curl http://localhost:8000/api/v1/status
  ```
- **POST Request**: Update the status (e.g., to "not OK").
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"status": "not OK"}' http://localhost:8000/api/v1/status
  ```