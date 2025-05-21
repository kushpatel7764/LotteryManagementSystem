from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)


@app.route('/scan_tickets.html', methods=["GET", "POST"])
def scan_tickets():
    return render_template('scan_tickets.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/initialize-database')
def initialize_database():
    return "Database initialized successfully. <a href='/'>Return Home</a>"

if __name__ == '__main__':
    app.run(debug=True)