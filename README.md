# Measurement Conversion API

This is a FastAPI application that provides an API for a custom measurement conversion logic. It also saves the history of all conversions to a MySQL database.

## Features

- Converts a string of characters into a list of numerical values based on a specific set of rules.
- Special handling for the character 'z'.
- Exposes the conversion logic via a RESTful API (GET and POST).
- Persists all conversion requests and results to a MySQL database.
- Provides an API endpoint to retrieve the entire conversion history.
- Containerized with Docker and orchestrated with Docker Compose.
- Comprehensive logging to both console and a log file (`app.log`).

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

To get the application up and running, follow these simple steps:

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Run with Docker Compose

Once you are in the project's root directory (the one containing `docker-compose.yml`), run the following command:

```bash
docker-compose up --build
```

This command will:
- Build the Docker image for the FastAPI application as defined in the `Dockerfile`.
- Start two containers: one for the FastAPI application (`app`) and one for the MySQL database (`db`).
- The `app` service will wait for the `db` service to be healthy before starting.
- The application will be accessible at `http://localhost:8090`.

### 3. Access the API

The API will be running and available at `http://localhost:8090`. You can access the interactive API documentation (Swagger UI) at `http://localhost:8090/docs`.

## API Endpoints

The following endpoints are available:

### Convert Measurements

- **POST** `/convert-measurements`
  - Processes a string and returns the conversion result.
  - **Request Body:**
    ```json
    {
      "input_str": "your_string_here"
    }
    ```
  - **Response:**
    ```json
    {
      "input_str": "your_string_here",
      "result": [ ... ]
    }
    ```

- **GET** `/convert-measurements`
  - Processes a string and returns the conversion result.
  - **Query Parameter:** `input_str`
  - **Example:** `http://localhost:8090/convert-measurements?input_str=your_string_here`
  - **Response:**
    ```json
    {
      "input_str": "your_string_here",
      "result": [ ... ]
    }
    ```

### History

- **GET** `/history`
  - Retrieves a list of all past conversion requests and their results.
  - **Response:** A JSON array of history objects.
    ```json
    [
      {
        "id": 1,
        "input_str": "abcee",
        "result": {
          "result": [2, 10]
        },
        "timestamp": "2025-09-29T10:00:00.000Z"
      },
      ...
    ]
    ```

## Database

The application uses a MySQL database to store the history of conversions. The database is configured in the `docker-compose.yml` file.

- **Service name:** `db`
- **Database:** `app_db`
- **User:** `app_user`
- **Password:** `password`

The data is persisted in a Docker volume named `mysql_data` to ensure data is not lost when the containers are stopped or removed.

## Logging

- Logs are printed to the console (stdout) of the `app` container. You can view them by running `docker-compose logs -f app`.
- Logs are also written to a file named `app.log` inside the project directory. The log file is rotated weekly, and a retention period of two weeks is configured.
