import serial
import json
import threading
import csv
import os
import time
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, Response
from datetime import datetime
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import io

app = Flask(__name__)
app.secret_key = 'doctor_secret_key_2024'

# Doctor credentials
VALID_DOCTORS = {
    'doctor1': 'password123',
    'doctor2': 'health456'
}

# Shared data
health_data = {
    "bpm": 72,
    "spo2": 96,
    "audio": 45,
    "temperature": 36.5,
    "humidity": 45,
    "status": "Initializing..."
}
health_history = []
cough_events = []

CSV_FILE = "health_data.csv"
CSV_HEADERS = ["time", "bpm", "spo2", "audio", "temperature", "humidity"]
csv_lock = threading.Lock()

# ============ ENSURE CSV FILE & HEADERS ============
# If the CSV already exists but has an older header, rewrite it in-place to include the new columns.
def ensure_csv_headers():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS)
        return

    with open(CSV_FILE, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    if not rows:
        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS)
        return

    if rows[0] != CSV_HEADERS:
        new_rows = [CSV_HEADERS]
        for r in rows[1:]:
            padded = r + [""] * (len(CSV_HEADERS) - len(r))
            new_rows.append(padded[:len(CSV_HEADERS)])
        with open(CSV_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(new_rows)

ensure_csv_headers()

# ============ ML MODEL ============
scaler = StandardScaler()
health_risk_model = RandomForestClassifier(n_estimators=10, random_state=42)

dummy_X = np.random.randn(100, 3)
dummy_y = np.random.randint(0, 3, 100)
health_risk_model.fit(dummy_X, dummy_y)

# ============ SERIAL READING THREAD ============
def read_serial():
    global health_data, health_history, cough_events
    import time as time_module
    
    try:
        ser = serial.Serial('COM6', 115200, timeout=1)
        serial_connected = True
    except Exception as e:
        print(f"Serial Error: {e} - Using Mock Data Instead")
        serial_connected = False
        health_data["status"] = "📊 Using Test Data"

    while True:
        try:
            if serial_connected:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    data = json.loads(line)

                    # Map sensor payload keys to our internal field names
                    if 'cough' in data:
                        data['audio'] = data.pop('cough')
                    if 'temp' in data:
                        data['temperature'] = data.pop('temp')
                    if 'hum' in data:
                        data['humidity'] = data.pop('hum')

                    health_data.update(data)
            else:
                # Generate realistic mock data
                health_data["bpm"] = int(70 + np.random.normal(0, 5))
                health_data["spo2"] = int(96 + np.random.normal(0, 2))
                health_data["audio"] = int(max(0, 50 + np.random.normal(0, 30)))
                health_data["temperature"] = round(36.5 + np.random.normal(0, 0.3), 1)
                health_data["humidity"] = int(max(20, min(90, 45 + np.random.normal(0, 5))))
                time_module.sleep(1)

            # Cough Detection Logic
            if health_data["audio"] > 350:
                health_data["status"] = "⚠️ Coughing Detected"
                cough_events.append({
                    'time': datetime.now().isoformat(),
                    'intensity': health_data["audio"]
                })
            else:
                health_data["status"] = "✅ Normal Breathing"

            # Store in memory
            record = {
                'time': datetime.now().isoformat(),
                'bpm': health_data["bpm"],
                'spo2': health_data["spo2"],
                'audio': health_data["audio"],
                'temperature': health_data.get("temperature", ""),
                'humidity': health_data.get("humidity", "")
            }

            health_history.append(record)

            # Keep only last 1000 records in RAM
            if len(health_history) > 1000:
                health_history.pop(0)

            # ============ SAVE TO CSV ============
            with csv_lock:
                with open(CSV_FILE, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        record['time'],
                        record['bpm'],
                        record['spo2'],
                        record['audio'],
                        record['temperature'],
                        record['humidity']
                    ])

        except Exception as e:
            if serial_connected:
                print(f"Read error: {e}")
            continue

# ============ AUTH ROUTES ============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in VALID_DOCTORS and VALID_DOCTORS[username] == password:
            session['doctor_name'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('doctor_name', None)
    return redirect(url_for('login'))

# ============ MAIN ROUTES ============
@app.route('/')
def index():
    if 'doctor_name' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'doctor_name' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', doctor=session['doctor_name'])

@app.route('/analysis')
def analysis():
    if 'doctor_name' not in session:
        return redirect(url_for('login'))
    return render_template('analysis.html', doctor=session['doctor_name'])

# ============ API ROUTES ============
@app.route('/api/data')
def get_data():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(health_data)

@app.route('/api/history')
def get_history():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(health_history[-100:])

@app.route('/api/cough-events')
def get_cough_events():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(cough_events[-20:])

# ============ CSV DOWNLOAD ROUTE ============
@app.route('/api/download-csv')
def download_csv():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if not os.path.exists(CSV_FILE):
        return jsonify({"error": "CSV file not found"}), 404

    # Take a snapshot under lock so the response is fast and consistent.
    with csv_lock:
        with open(CSV_FILE, "r", newline="") as file:
            csv_content = file.read()

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=health_data.csv"}
    )

# ============ HEALTH RISK API ============
@app.route('/api/health-risk', methods=['POST'])
def calculate_health_risk():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        bpm = float(data.get('bpm', 70))
        spo2 = float(data.get('spo2', 95))
        audio = float(data.get('audio', 0))

        X = np.array([[bpm, spo2, audio]])
        risk_level = health_risk_model.predict(X)[0]
        risk_names = {0: 'Normal', 1: 'Warning', 2: 'Critical'}

        if bpm < 40 or bpm > 120:
            risk_level = max(risk_level, 1)
        if spo2 < 90:
            risk_level = 2
        if audio > 350:
            risk_level = max(risk_level, 1)

        return jsonify({
            'risk_level': risk_names[risk_level],
            'bpm': bpm,
            'spo2': spo2,
            'audio': audio,
            'recommendations': get_recommendations(bpm, spo2, audio)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

def get_recommendations(bpm, spo2, audio):
    recommendations = []

    if bpm < 40:
        recommendations.append("Low heart rate - Check vitals")
    elif bpm > 120:
        recommendations.append("High heart rate - Patient stressed/exercising")

    if spo2 < 90:
        recommendations.append("⚠️ Low oxygen - Immediate attention needed")
    elif spo2 < 95:
        recommendations.append("SpO2 slightly low - Monitor closely")

    if audio > 350:
        recommendations.append("Cough detected - Possible respiratory issue")
    elif audio > 200:
        recommendations.append("Elevated cough signal - Monitor breathing")

    if not recommendations:
        recommendations.append("Patient vitals are stable")

    return recommendations
# ============ DISEASE PREDICTION API ============
def predict_diseases(bpm, spo2, audio):
    """Predicts diseases based on vitals - shows common, non-severe conditions"""
    diseases = []
    
    # Normal range
    if 60 <= bpm <= 100 and 95 <= spo2 <= 100 and audio < 100:
        return {"status": "Healthy", "probability": 0.95, "diseases": []}
    
    # Minor Coughing
    if 50 < audio <= 200:
        diseases.append({
            "name": "Minor Coughing",
            "probability": 0.70,
            "description": "Mild cough detected - possibly from allergens or dry air",
            "severity": "mild"
        })
    
    # General Infection (fever-like symptoms)
    if (100 < bpm <= 120 and spo2 >= 92 and audio > 100):
        diseases.append({
            "name": "General Infection",
            "probability": 0.65,
            "description": "Elevated vital signs suggesting possible infection - monitor symptoms",
            "severity": "mild"
        })
    
    # Throat Illness
    if (audio > 150 and spo2 >= 90 and bpm < 110):
        diseases.append({
            "name": "Throat Illness",
            "probability": 0.60,
            "description": "Cough or throat sounds detected - may indicate sore throat or pharyngitis",
            "severity": "mild"
        })
    
    # Common Cold
    if (100 < bpm <= 110 and audio > 80):
        diseases.append({
            "name": "Common Cold",
            "probability": 0.55,
            "description": "Symptoms consistent with common cold or mild respiratory infection",
            "severity": "mild"
        })
    
    # Mild Respiratory Congestion
    if 150 < audio <= 280:
        diseases.append({
            "name": "Mild Respiratory Congestion",
            "probability": 0.68,
            "description": "Nasal or chest congestion detected",
            "severity": "mild"
        })
    
    # Stress or Anxiety
    if (120 < bpm <= 140 and spo2 >= 93 and audio < 100):
        diseases.append({
            "name": "Stress or Anxiety",
            "probability": 0.50,
            "description": "Elevated heart rate may indicate stress-related condition",
            "severity": "mild"
        })
    
    # Low Oxygen Level (mild)
    if 90 <= spo2 < 95:
        diseases.append({
            "name": "Mild Hypoxemia",
            "probability": 0.60,
            "description": "Slightly reduced oxygen levels - consider increase physical activity",
            "severity": "mild"
        })
    
    # Asthma-like Symptoms
    if (audio > 200 and bpm > 100 and spo2 < 96):
        diseases.append({
            "name": "Asthma-like Symptoms",
            "probability": 0.55,
            "description": "Respiratory distress patterns detected - consult for proper evaluation",
            "severity": "mild"
        })
    
    # Filter out only mild/moderate diseases
    mild_diseases = [d for d in diseases if d["severity"] in ["mild", "moderate"]]
    
    if not mild_diseases:
        return {"status": "Normal", "probability": 0.85, "diseases": []}
    
    # Sort by probability
    mild_diseases.sort(key=lambda x: x["probability"], reverse=True)
    
    return {
        "status": "Monitor",
        "probability": min(0.95, mild_diseases[0]["probability"]),
        "diseases": mild_diseases[:3]  # Top 3 diseases
    }

@app.route('/api/predict-disease', methods=['POST'])
def disease_prediction():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        bpm = float(data.get('bpm', 70))
        spo2 = float(data.get('spo2', 95))
        audio = float(data.get('audio', 0))

        result = predict_diseases(bpm, spo2, audio)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ============ CSV UPLOAD AND ANALYSIS ============
@app.route('/api/analyze-csv', methods=['POST'])
def analyze_csv():
    if 'doctor_name' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files allowed"}), 400
        
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        csv_data = []
        headers = None
        
        for i, line in enumerate(stream):
            if i == 0:
                headers = [h.strip() for h in line.split(',')]
            else:
                values = [v.strip() for v in line.split(',')]
                csv_data.append(dict(zip(headers, values)))
        
        if not csv_data:
            return jsonify({"error": "CSV file is empty"}), 400
        
        # Extract vital signs - handle different column names
        bpm_values = []
        spo2_values = []
        audio_values = []
        
        for row in csv_data:
            try:
                # Find BPM column
                bpm_col = next((k for k in row.keys() if 'bpm' in k.lower()), None)
                if bpm_col:
                    bpm_values.append(float(row[bpm_col]) if row[bpm_col] else 0)
                
                # Find SpO2 column
                spo2_col = next((k for k in row.keys() if 'spo2' in k.lower() or 'oxygen' in k.lower()), None)
                if spo2_col:
                    spo2_values.append(float(row[spo2_col]) if row[spo2_col] else 0)
                
                # Find Audio/Cough column
                audio_col = next((k for k in row.keys() if 'audio' in k.lower() or 'cough' in k.lower()), None)
                if audio_col:
                    audio_values.append(float(row[audio_col]) if row[audio_col] else 0)
            except:
                continue
        
        # Calculate averages
        avg_bpm = np.mean(bpm_values) if bpm_values else 70
        avg_spo2 = np.mean(spo2_values) if spo2_values else 95
        avg_audio = np.mean(audio_values) if audio_values else 0
        
        # Get predictions
        disease_result = predict_diseases(avg_bpm, avg_spo2, avg_audio)
        
        return jsonify({
            "success": True,
            "avg_bpm": round(avg_bpm, 2),
            "avg_spo2": round(avg_spo2, 2),
            "avg_audio": round(avg_audio, 2),
            "records_analyzed": len(csv_data),
            "diseases": disease_result["diseases"],
            "status": disease_result["status"]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
# ============ RUN APP ============
if __name__ == '__main__':
    threading.Thread(target=read_serial, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)