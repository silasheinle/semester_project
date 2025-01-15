from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Route für die Startseite
@app.route('/')
def index():
    conn = sqlite3.connect('weatherstation.db')
    cursor = conn.cursor()

    # Query: Holen der neuesten Werte je Station
    query = """
    SELECT 
        s.station_id,
        s.longitude,
        s.latitude,
        m.wind_speed,
        m.wind_direction,
        m.pressure,
        m.humidity,
        m.temperature,
        m.timestamp
    FROM stations s
    LEFT JOIN (
        SELECT * FROM measurements
        WHERE timestamp IN (
            SELECT MAX(timestamp)
            FROM measurements
            GROUP BY station_id
        )
    ) m ON s.station_id = m.station_id
    ORDER BY m.timestamp DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    formatted_data = [
        {
            "station_id": row[0],
            "longitude": row[1],
            "latitude": row[2],
            "windSpeed": row[3],
            "windDirection": row[4],
            "pressure": row[5],
            "humidity": row[6],
            "temperature": row[7],
            "timestamp": row[8],
        }
        for row in data
    ]
    return render_template('index.html', data=formatted_data)

# API-Route für das Filtern von Daten
@app.route('/api/filter', methods=['GET'])
def filter_data():
    try:
        time_filter = request.args.get('filter', '24h')  # Standardfilter: letzte 24h
        time_conditions = {
            '24h': "DATETIME('now', '-1 day')",
            '5d': "DATETIME('now', '-5 days')",
            '7d': "DATETIME('now', '-7 days')"
        }

        if time_filter not in time_conditions:
            return jsonify({"error": "Ungültiger Filter"}), 400

        conn = sqlite3.connect('weatherstation.db')
        cursor = conn.cursor()

        # Aktuelle Werte je Station
        latest_query = """
        SELECT 
            s.station_id,
            s.longitude,
            s.latitude,
            m.wind_speed,
            m.wind_direction,
            m.pressure,
            m.humidity,
            m.temperature,
            m.timestamp
        FROM stations s
        LEFT JOIN (
            SELECT * FROM measurements
            WHERE timestamp IN (
                SELECT MAX(timestamp)
                FROM measurements
                GROUP BY station_id
            )
        ) m ON s.station_id = m.station_id
        """
        cursor.execute(latest_query)
        latest_data = cursor.fetchall()

        # AVG-Werte entsprechend Filter
        avg_query = f"""
        SELECT 
            s.station_id,
            AVG(m.wind_speed) AS avgWindSpeed,
            (SELECT m2.wind_direction
             FROM measurements m2
             WHERE m2.station_id = s.station_id AND m2.timestamp >= {time_conditions[time_filter]}
             GROUP BY m2.wind_direction
             ORDER BY COUNT(m2.wind_direction) DESC
             LIMIT 1) AS mostCommonWindDirection,
            AVG(m.pressure) AS avgPressure,
            AVG(m.humidity) AS avgHumidity,
            AVG(m.temperature) AS avgTemperature
        FROM measurements m
        INNER JOIN stations s ON m.station_id = s.station_id
        WHERE m.timestamp >= {time_conditions[time_filter]}
        GROUP BY s.station_id
        """
        cursor.execute(avg_query)
        avg_data = cursor.fetchall()

        conn.close()

        # Formatierte Ergebnisse
        latest_formatted = [
            {
                "station_id": row[0],
                "longitude": row[1],
                "latitude": row[2],
                "windSpeed": row[3],
                "windDirection": row[4],
                "pressure": row[5],
                "humidity": row[6],
                "temperature": row[7],
                "timestamp": row[8]
            } for row in latest_data
        ]

        avg_formatted = {row[0]: {
            "avgWindSpeed": row[1] or 0,
            "mostCommonWindDirection": row[2] or "N/A",
            "avgPressure": row[3] or 0,
            "avgHumidity": row[4] or 0,
            "avgTemperature": row[5] or 0,
        } for row in avg_data}

        return jsonify({"latest": latest_formatted, "avg": avg_formatted}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API-Route für das Hinzufügen von Messwerten
@app.route('/api/measurements', methods=['POST'])
def add_measurement():
    try:
        data = request.get_json()

        required_fields = [
            'station_id', 'longitude', 'latitude',
            'wind_speed', 'wind_direction', 'pressure',
            'humidity', 'temperature'
        ]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "incomplete input"}), 400

        station_id = data['station_id']
        longitude = data['longitude']
        latitude = data['latitude']
        wind_speed = data['wind_speed']
        wind_direction = data['wind_direction']
        pressure = data['pressure']
        humidity = data['humidity']
        temperature = data['temperature']

        conn = sqlite3.connect('weatherstation.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM stations WHERE station_id = ?", (station_id,))
        station = cursor.fetchone()

        if not station:
            cursor.execute("""
                INSERT INTO stations (station_id, longitude, latitude) 
                VALUES (?, ?, ?)
            """, (station_id, longitude, latitude))

        cursor.execute("""
            INSERT INTO measurements (station_id, wind_speed, wind_direction, pressure, humidity, temperature, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, DATETIME('now', 'localtime'))
        """, (station_id, wind_speed, wind_direction, pressure, humidity, temperature))

        conn.commit()
        conn.close()

        new_data = {
            "station_id": station_id,
            "longitude": longitude,
            "latitude": latitude,
            "windSpeed": wind_speed,
            "windDirection": wind_direction,
            "pressure": pressure,
            "humidity": humidity,
            "temperature": temperature,
            "timestamp": "now",
        }
        socketio.emit('new_measurement', new_data)

        return jsonify({"message": "Daten erfolgreich hinzugefügt"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
