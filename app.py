from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.metrics import set_meter_provider, get_meter

# Init Flask app and configure database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
db = SQLAlchemy(app)

## OpenTelemetry setup
resource = Resource(attributes={"service.name": "crud-app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Use OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Flask and SQLAlchemy instrumentation
FlaskInstrumentor().instrument_app(app)
with app.app_context():
    SQLAlchemyInstrumentor().instrument(engine=db.engine)


# Create a PeriodicExportingMetricReader with ConsoleMetricExporter
metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())

# Init the MeterProvider with the metric reader
meter_provider = MeterProvider(metric_readers=[metric_reader])

# Set global meter provider
set_meter_provider(meter_provider)

# Create a meter
meter = get_meter(__name__)
request_counter = meter.create_counter("requests", description="Number of requests received")



# Database model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}

# init database
with app.app_context():
    db.create_all()


# CRUD operation routes
@app.route("/items", methods=["POST"])
def create_item():
    with tracer.start_as_current_span("create_item"):
        data = request.get_json()
        if not data or not "name" in data:
            abort(400, description="Name is required")
        item = Item(name=data["name"], description=data.get("description", ""))
        db.session.add(item)
        db.session.commit()
        request_counter.add(1, {"method": "POST", "endpoint": "/items"})
        return jsonify(item.to_dict()), 201

@app.route("/items", methods=["GET"])
def get_items():
    with tracer.start_as_current_span("get_items"):
        items = Item.query.all()
        request_counter.add(1, {"method": "GET", "endpoint": "/items"})
        return jsonify([item.to_dict() for item in items])

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    with tracer.start_as_current_span("get_item"):
        item = Item.query.get_or_404(item_id)
        request_counter.add(1, {"method": "GET", "endpoint": f"/items/{item_id}"})
        return jsonify(item.to_dict())

@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    with tracer.start_as_current_span("update_item"):
        data = request.get_json()
        item = Item.query.get_or_404(item_id)
        item.name = data.get("name", item.name)
        item.description = data.get("description", item.description)
        db.session.commit()
        request_counter.add(1, {"method": "PUT", "endpoint": f"/items/{item_id}"})
        return jsonify(item.to_dict())

@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    with tracer.start_as_current_span("delete_item"):
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        request_counter.add(1, {"method": "DELETE", "endpoint": f"/items/{item_id}"})
        return jsonify({"message": "Item deleted"})

# exec the app
if __name__ == "__main__":
    app.run(debug=True)

