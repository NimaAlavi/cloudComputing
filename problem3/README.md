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

   Upon running the container, you should see output indicating that the server has started successfully, similar to:
   ```
   * Serving Flask app 'server'
   * Debug mode: off
   WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:8000
   * Running on http://172.17.0.2:8000
   Press CTRL+C to quit
   ```

   Once the server is running, you can verify its functionality using the commands in the "Verifying the Server" section below. The server logs will also show request handling, such as:
   ```
   172.17.0.1 - - [14/Jul/2025 16:07:57] "GET /api/v1/status HTTP/1.1" 200 -
   172.17.0.1 - - [14/Jul/2025 16:08:02] "POST /api/v1/status HTTP/1.1" 201 -
   ```

## Verifying the Server

After starting the server (either locally or via Docker), you can verify its functionality with the following commands:

1. **Retrieve the initial status**:
   ```bash
   curl http://localhost:8000/api/v1/status
   ```
   Expected output:
   ```json
   {"status":"OK"}
   ```

2. **Update the status**:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"status": "not OK"}' http://localhost:8000/api/v1/status
   ```
   Expected output:
   ```json
   {"status":"not OK"}
   ```

3. **Retrieve the updated status**:
   ```bash
   curl http://localhost:8000/api/v1/status
   ```
   Expected output:
   ```json
   {"status":"not OK"}
   ```