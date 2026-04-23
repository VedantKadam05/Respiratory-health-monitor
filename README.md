# 🏥 Health Monitoring IoT System

A comprehensive real-time health monitoring system for healthcare professionals with ML-based risk assessment, built with Flask and IoT device integration.

## Features

### 🔐 **Authentication**
- Doctor-only access with secure login
- Username/password authentication
- Session management
- Demo credentials for testing:
  - `doctor1` / `password123`
  - `doctor2` / `health456`

### 📊 **Dashboard**
Real-time monitoring of patient vital signs:
- **Heart Rate (BPM)** - Cardiac monitoring with normal/warning thresholds
- **Oxygen Saturation (SpO2)** - Respiratory health measurement
- **Cough Detection** - Audio-based respiratory symptom analysis
- Live charts with real-time data visualization
- Automatic status alerts based on vital thresholds

### 🔬 **Analysis Page**
Machine Learning-based health risk assessment:
- ML model for health risk prediction (Normal/Warning/Critical)
- Custom vital sign analyzer
- Clinical recommendations based on ML predictions
- Historical trend visualization
- Risk assessment with rule-based augmentation

### 💾 **Data Management**
- Real-time data collection from serial IoT devices
- Historical data logging (last 1000 records)
- Cough event tracking
- Data API endpoints for analysis

## System Requirements

- Python 3.8+
- Flask 2.3.0
- scikit-learn (for ML models)
- numpy (for numerical operations)
- pyserial (for Arduino/IoT device communication)

## Installation

1. **Clone/Download the project**
```bash
cd ML_IOT_mini_project
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# OR
source .venv/bin/activate  # On Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Configuration

### Serial Port Setup
Update the COM port in `app.py` (Line 33):
```python
ser = serial.Serial('COM6', 115200, timeout=1)  # Change COM6 to your device's COM port
```

### Doctor Credentials
Modify the `VALID_DOCTORS` dictionary in `app.py` for production use:
```python
VALID_DOCTORS = {
    'doctor1': 'password123',
    'doctor2': 'health456'
}
```

## Running the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Doctor | doctor1 | password123 |
| Doctor | doctor2 | health456 |

## API Endpoints

### Authentication
- `POST /login` - Doctor login
- `GET /logout` - Doctor logout

### Dashboard
- `GET /dashboard` - Main monitoring dashboard
- `GET /api/data` - Current vital signs data (JSON)
- `GET /api/history` - Last 100 historical records

### Analysis
- `GET /analysis` - ML analysis page
- `POST /api/health-risk` - ML risk assessment
  - Request body: `{"bpm": 70, "spo2": 95, "audio": 0}`
  - Response: Risk level, recommendations

### Cough Detection
- `GET /api/cough-events` - Last 20 cough events

## Data Format

### Vital Signs (JSON)
```json
{
  "bpm": 72,
  "spo2": 98,
  "audio": 150,
  "status": "✅ Normal Breathing"
}
```

### Risk Assessment Response
```json
{
  "risk_level": "Normal",
  "bpm": 70,
  "spo2": 95,
  "audio": 0,
  "recommendations": ["Patient vitals are stable"]
}
```

## ML Model Details

### Health Risk Classification
The system uses a Random Forest Classifier trained on:
- BPM (Heart Rate)
- SpO2 (Oxygen Saturation)
- Audio Signal (Cough Detection)

### Risk Levels
1. **Normal (0)** - All vitals within healthy ranges
2. **Warning (1)** - One or more vitals slightly abnormal
3. **Critical (2)** - Severe abnormalities requiring immediate attention

### Decision Rules
- **BPM**: Normal 60-100, Warning 40-120, Critical <40 or >120
- **SpO2**: Normal >95%, Warning 90-95%, Critical <90%
- **Cough**: Detected >350dB, High Risk >200dB

## Project Structure

```
ML_IOT_mini_project/
├── app.py                      # Flask application & ML backend
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
└── templates/
    ├── login.html             # Doctor login page
    ├── dashboard.html         # Real-time monitoring
    └── analysis.html          # ML analysis & risk assessment
```

## Features in Detail

### 🎨 Dashboard Highlights
- Real-time vital sign cards with color-coded status
- Interactive charts using Chart.js
- Auto-updating data every 500ms
- Status alerts and notifications
- Responsive design for all devices

### 🤖 ML Analysis Features
- Manual vital input for analysis
- Automatic risk level prediction
- Clinical recommendations
- Historical trend analysis
- Real-time data integration

### 📱 Responsive Design
- Mobile-friendly interface
- Tablet optimized layouts
- Desktop full-feature experience
- Touch-friendly navigation

## Serial Data Format

Expected JSON format from IoT device (via Serial):
```json
{"bpm": 72, "spo2": 98, "audio": 150}
```

## Troubleshooting

### Serial Port Connection Error
- Verify COM port number matches device
- Check USB connection
- Ensure pyserial is installed
- Check device baudrate (default: 115200)

### Login Not Working
- Clear browser cookies
- Check Flask session secret key
- Verify credentials in app.py

### ML Model Not Responding
- Ensure scikit-learn is installed
- Check numpy installation
- Verify sufficient RAM for model training

## Security Notes

⚠️ **For Production Use:**
- Replace hardcoded credentials with database
- Use proper password hashing (bcrypt, argon2)
- Implement HTTPS/SSL
- Add CSRF protection
- Implement proper logging
- Use environment variables for secrets

## Future Enhancements

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Multiple patient support
- [ ] Advanced ML models (LSTM for time-series)
- [ ] Email/SMS alerts
- [ ] Data export (PDF/CSV)
- [ ] Admin dashboard
- [ ] Real-time notifications
- [ ] Patient data management

## License

MIT License - Free for educational and commercial use

## Support

For issues or questions, please refer to the documentation or check the Flask/scikit-learn official documentation.

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Developer**: Health Monitoring Team
