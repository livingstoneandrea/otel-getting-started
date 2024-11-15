# OpenTelemetry get started app

## Installation & setup
To install and set up this project
First of all, download and install python 3.8 or higher is required.

### Prerequisites
 - Python > v3.8
 - SQLite database
 - opentelemetry
 - local Jaeger instance
 - Docker

  
### Running the Project
  clone the repo, 

  install the dependencies
```shell

pip install Flask Flask-SQLAlchemy opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-flask opentelemetry-instrumentation-sqlalchemy opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

```
or use  requirement.txt

```shell
pip install -r requirement.txt
```

## App description

**OpenTelemetry Tracing**: The app uses opentelemetry.instrumentation.flask and opentelemetry.instrumentation.sqlalchemy to automatically trace requests and database operations. Traces are sent to Jaeger (or another backend if configured).

**OpenTelemetry Metrics**: The app includes a basic request counter using OpenTelemetry's metrics API. The counter logs the number of requests made to each endpoint and outputs to the console for now. You can configure this to use other exporters as needed

**Database**: SQLAlchemy manages the SQLlite Item table with columns id, name, and description

### Running the Application

1) Run a local Jaeger instance with OTLP support to collect traces:
    ```shel
    docker run -d --name jaeger \
        -e COLLECTOR_OTLP_ENABLED=true \
        -p 6831:6831/udp \
        -p 16686:16686 \
        -p 4317:4317 \
        jaegertracing/all-in-one:1.35

    ```

2) Start the Flask app
    ```shell
    python app.py
    ```
3) Access the Jaeger UI at http://localhost:16686 to view the traces.
