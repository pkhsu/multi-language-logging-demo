# Microservices Log Demo

## Overview

This repository demonstrates a **multi-language microservices** setup with **Docker Compose**, showcasing how logs can be collected and displayed in a standardized JSON format. The call flow is:

1. **Streamlit App** (port 8501) – User interface that triggers a button
2. **Python App** (Flask, port 5001) – Receives REST calls from Streamlit
3. **Node.js App** (port 3000) – Invoked by Python
4. **Golang App** (port 4000) – Invoked by Node.js
5. **Java App** (Spring Boot, port 8080) – Invoked by Golang

Each service outputs JSON logs with fields like `timestamp`, `level`, `service`, `instance`, `correlationId`, `message`, and `context`.

## How It Works

1. The user opens the **Streamlit** interface (usually <http://localhost:8501>).
2. When the user clicks a button, Streamlit calls the Python service at `http://python_app:5001/<endpoint>`.
3. The **Python** service then calls the **Node.js** endpoint, e.g. `http://nodejs_app:3000/node-hello`.
4. The **Node.js** service proceeds to call the **Golang** endpoint at `http://golang_app:4000/go-hello`.
5. Finally, the **Golang** service calls the **Java** endpoint at `http://javaapp:8080/java-hello`.
6. Each service logs its own messages in a consistent JSON format, so you can track the entire chain in logs.

## Usage: Starting the Services

1. Make sure you have **Docker** and **Docker Compose** installed.
2. Clone this repository and navigate into it.
3. Run:
   ```bash
   docker compose build
   docker compose up -d
   ```
4. After the containers start, open your browser to <http://localhost:8501> (or the corresponding IP/port if running in a different environment) to access the Streamlit app.
5. Click the button in Streamlit to trigger the entire chain (Python → Node.js → Golang → Java) call flow.
6. Logs from each service will be visible in Docker logs (`docker logs <container_name>`), or in the Streamlit UI if it fetches them via `subprocess`.

## Docker Compose File Explanation

Below is the `docker-compose.yml` used to define the services:

```yaml
version: "3.9"

services:
  python_app:
    container_name: python_app_container
    build: ./python_app
    ports:
      - "5001:5001"
    depends_on:
      - nodejs_app
      - golang_app
      - javaapp

  nodejs_app:
    container_name: nodejs_app_container
    build: ./nodejs_app
    ports:
      - "3000:3000"
    depends_on:
      - golang_app
      - javaapp

  golang_app:
    container_name: golang_app_container
    build: ./golang_app
    ports:
      - "4000:4000"
    depends_on:
      - javaapp

  javaapp:
    container_name: java_app_container
    build: ./java_app
    ports:
      - "8080:8080"

  streamlit_app:
    container_name: streamlit_app_container
    build: ./streamlit_app
    ports:
      - "8501:8501"
    depends_on:
      - python_app
      - nodejs_app
      - golang_app
      - javaapp
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

### Service Details

- **python\_app**
  - A simple Flask app (port 5001). Handles initial REST calls from Streamlit.

- **nodejs\_app**
  - A Node.js app (port 3000). Called by Python to demonstrate chaining and logs.

- **golang\_app**
  - A Go app (port 4000). Invoked by Node.js, outputs JSON logs via zap.

- **javaapp**
  - A Java (Spring Boot) service (port 8080). Final link in the chain. Logs JSON using logstash-logback-encoder.

- **streamlit\_app**
  - A Streamlit frontend (port 8501) providing a simple UI with a button that kicks off the chain.
  - **volumes**: `- /var/run/docker.sock:/var/run/docker.sock` is optional and only needed if the Streamlit container must run `docker logs` directly to display container logs inside the UI.

### depends\_on

The `depends_on` directive ensures that certain containers are started before others, but it does not guarantee the internal app is fully ready. Still, it’s a helpful way to control startup order. If an app needs more time to initialize, you may need additional health checks or a retry mechanism.

---

## Conclusion

By running `docker compose up -d`, you’ll launch **five** containers that illustrate a multi-language microservice call chain. You can then see how each service logs in **JSON** format, making it easier to trace requests and handle centralized logging. Enjoy exploring the chain from **Streamlit** to **Python** to **Node.js** to **Golang** to **Java**!