#!/usr/bin/env python3

import pandas as pd
import random
import os
import re
import sys
import boto3
from datetime import datetime
from pathlib import Path

def generate_sensor_data(device_id, date):
    """Generate 24 hours of sensor readings for a device"""
    readings = []
    base_temp = 20 + random.random() * 10  # 20-30°C base
    base_humidity = 40 + random.random() * 30  # 40-70% base
    base_battery = 60 + random.random() * 40  # 60-100% base
    
    # Generate 24 hours of readings (every hour)
    for hour in range(24):
        # Add some variation
        temperature = base_temp + (random.random() - 0.5) * 4
        humidity = base_humidity + (random.random() - 0.5) * 10
        battery_level = base_battery - (hour * 1.5)  # Battery drains over time
        
        # Inject anomalies occasionally
        if random.random() < 0.05:  # 5% chance of temperature spike
            temperature = 40 + random.random() * 10 if random.random() < 0.5 else -15 + random.random() * 5
        if random.random() < 0.03:  # 3% chance of humidity anomaly
            humidity = 98 + random.random() * 2 if random.random() < 0.5 else 2 + random.random() * 3
        
        readings.append({
            'deviceid': device_id,
            'timestamp': f'{date}T{hour:02d}:00:00Z',
            'temperature': round(temperature, 2),
            'humidity': round(humidity, 2),
            'batterylevel': max(0, round(battery_level, 2)),
            'latitude': 37.7749 + (random.random() - 0.5) * 0.1,
            'longitude': -122.4194 + (random.random() - 0.5) * 0.1
        })
    
    return readings

def upload_to_s3(local_file, bucket_name, s3_key):
    """Upload file to S3 using boto3"""
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(str(local_file), bucket_name, s3_key)
    except Exception as e:
        print(f"Error uploading {local_file} to s3://{bucket_name}/{s3_key}")
        print(f"Error: {e}")
        sys.exit(1)

def validate_bucket_name(bucket_name):
    """Validate S3 bucket name to prevent injection attacks"""
    if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket_name):
        print("Error: Invalid bucket name. Must contain only lowercase letters, numbers, dots, and hyphens.")
        sys.exit(1)
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        print("Error: Bucket name must be between 3 and 63 characters.")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_sample_data.py <s3-bucket-name>")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    validate_bucket_name(bucket_name)
    today = datetime.now().strftime('%Y-%m-%d')
    device_ids = ['sensor-001', 'sensor-002', 'sensor-003', 'sensor-004', 'sensor-005']
    
    # Create local directories
    data_dir = Path('temp_data')
    daily_dir = data_dir / 'daily-data' / today
    # manifest_dir = data_dir / 'manifests' / 'daily'
    
    daily_dir.mkdir(parents=True, exist_ok=True)
    # manifest_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating sample IoT data for {len(device_ids)} devices...")
    
    created_files = []
    
    # Generate CSV files for each device
    for device_id in device_ids:
        print(f"Generating data for {device_id}...")
        sensor_data = generate_sensor_data(device_id, today)
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(sensor_data)
        csv_file = daily_dir / f'{device_id}.csv'
        df.to_csv(csv_file, index=False)
        
        s3_key = f'daily-data/{today}/{device_id}.csv'
        created_files.append(f's3://{bucket_name}/{s3_key}')
        
        print(f"  Generated {len(sensor_data)} readings")
    '''
    # Create Athena manifest file
    manifest_file = manifest_dir / 'sensor-data-manifest.csv'
    with open(manifest_file, 'w') as f:
        for s3_url in created_files:
            f.write(f'{s3_url}\n')
    '''
    print(f"\nUploading files to S3 bucket: {bucket_name}")
    
    # Upload CSV files
    for device_id in device_ids:
        local_file = daily_dir / f'{device_id}.csv'
        s3_key = f'daily-data/{today}/{device_id}.csv'
        
        print(f"Uploading {device_id}.csv...")
        upload_to_s3(local_file, bucket_name, s3_key)
    '''
    # Upload manifest file
    manifest_s3_key = 'manifests/daily/sensor-data-manifest.csv'
    print("Uploading manifest file...")
    upload_to_s3(manifest_file, bucket_name, manifest_s3_key)
    '''
    # Clean up local files
    import shutil
    shutil.rmtree(data_dir)
    
    print(f"\n✅ Successfully generated and uploaded:")
    print(f"   - {len(device_ids)} CSV files")
    # print(f"   - 1 Athena manifest file")
    print(f"   - Total records: {len(device_ids) * 24}")
    # print(f"\nManifest location: s3://{bucket_name}/{manifest_s3_key}")

if __name__ == '__main__':
    main()