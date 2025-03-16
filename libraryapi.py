from flask import Flask, request, jsonify
import mysql.connector
import hashlib
import creds
from datetime import datetime, timedelta

app = Flask(__name__)

# Database Connection
DB_CONFIG = {
    'host': 'your_host',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'library_db'
}

