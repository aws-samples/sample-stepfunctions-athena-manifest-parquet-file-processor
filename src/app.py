import json
from datetime import datetime

def handler(event, context):
    print(f'Received event: {json.dumps(event, default=str)}')
    
    # Handle single sensor reading (from Distributed Map processing individual records)
    sensor_reading = event
    
    # Validate the sensor reading
    if not sensor_reading or not isinstance(sensor_reading, dict):
        return {
            'deviceId': 'unknown',
            'error': 'Invalid sensor reading data',
            'timestamp': datetime.now().isoformat()
        }
    
    # Extract values from the single reading
    device_id = sensor_reading.get('deviceId', 'unknown')
    temperature = sensor_reading.get('temperature')
    humidity = sensor_reading.get('humidity')
    battery_level = sensor_reading.get('batteryLevel')
    reading_timestamp = sensor_reading.get('timestamp')
    
    # Detect anomalies for this single reading
    anomalies = []
    
    # Temperature spike detection (> 35°C or < -10°C)
    if temperature is not None and (temperature > 35 or temperature < -10):
        anomalies.append({
            'type': 'temperature_spike',
            'value': temperature,
            'threshold': '>35°C' if temperature > 35 else '<-10°C'
        })
    
    # Humidity anomaly detection (> 95% or < 5%)
    if humidity is not None and (humidity > 95 or humidity < 5):
        anomalies.append({
            'type': 'humidity_anomaly',
            'value': humidity,
            'threshold': '>95%' if humidity > 95 else '<5%'
        })
    
    # Low battery detection (< 20%)
    if battery_level is not None and battery_level < 20:
        anomalies.append({
            'type': 'low_battery',
            'value': battery_level,
            'threshold': '<20%'
        })
    
    # Extract analysis date from reading timestamp or use current date
    if reading_timestamp:
        analysis_date = reading_timestamp.split('T')[0]
    else:
        analysis_date = datetime.now().isoformat().split('T')[0]
    
    return {
        'deviceId': device_id,
        'analysisDate': analysis_date,
        'readingTimestamp': reading_timestamp,
        'readingsCount': 1,  # Single reading processed
        'metrics': {
            'temperature': round(temperature, 2) if temperature is not None else None,
            'humidity': round(humidity, 2) if humidity is not None else None,
            'batteryLevel': round(battery_level, 2) if battery_level is not None else None,
            'latitude': sensor_reading.get('latitude'),
            'longitude': sensor_reading.get('longitude')
        },
        'anomalies': anomalies,
        'anomalyCount': len(anomalies),
        'healthStatus': 'healthy' if len(anomalies) == 0 else 'anomalies_detected',
        'timestamp': datetime.now().isoformat()
    }
