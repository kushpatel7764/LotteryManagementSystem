import eventlet
eventlet.monkey_patch()
from flask_socketio import SocketIO
from flask import Flask,request
from routes.home import home_bp
from routes.reports import report_bp
from routes.tickets import tickets_bp
from routes.books import books_bp
from routes.settings import settings_bp
from routes.business_profile import business_profile_bp
app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")  # Allow all for dev

# Register blueprints
app.register_blueprint(home_bp)
app.register_blueprint(report_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(books_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(business_profile_bp)

@socketio.on('connect')
def on_connect():
    print("Client connected")

@app.route('/receive', methods=['POST'])
def receive():
    barcode = request.form.get('barcode')
    print(f"Received barcode: {barcode}")
    with app.app_context():
        socketio.emit("barcode_scanned", {"barcode": barcode})
    return "Received"


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    