from flask import Flask, request, render_template, jsonify, url_for
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import time
from models import *
app = Flask(__name__)

DB_USERNAME = "autogreen_user"  # Replace with your RDS username
DB_PASSWORD = "ILoveTheLibrary765$"  # Replace with your RDS password
DB_HOST = "autogreen-db-1.clk2q8i2c4nk.us-east-1.rds.amazonaws.com"  # Replace with your RDS endpoint
DB_PORT = "5432"  # Default PostgreSQL port
DB_NAME = "postgres"  # Replace with your database name

# SQLAlchemy configuration for RDS
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the SQLAlchemy db instance
db.init_app(app)
migrate = Migrate(app, db) 
jwt = JWTManager(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

@app.route('/')
def hello_world():
    print("got an api call")
    return 'Hello, World! Welcome to Autogreen bros!'

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"msg": "Missing username, password, or email"}), 400

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"msg": "Username already exists"}), 400

    new_user = User(username=username, email=email)
    new_user.password_hash = generate_password_hash(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User registered successfully"}), 200


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(
            identity={'username': user.username})
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad username or password"}), 401


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user_data = {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }
    return jsonify(user_data), 200


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if username:
        user.username = username

    if email:
        user.email = email

    if password:
        user.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify({"msg": "User updated successfully"}), 200


@app.route('/api/devices/register', methods=['POST'])
def register_device():
    data = request.get_json()
    user_id = data.get('user_id')
    plant_id = data.get('plant_id')
    device_name = data.get('device_name')

    if not user_id or not plant_id or not device_name:
        return jsonify({"msg": "Missing user_id, plant_id, or device_name"}), 400

    new_device = Device(user_id=user_id, plant_id=plant_id,
                        device_name=device_name)

    db.session.add(new_device)
    db.session.commit()

    return jsonify({"msg": "Device registered successfully", "device_id": new_device.device_id}), 200


@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    device = Device.query.get(device_id)
    if not device:
        return jsonify({"msg": "Device not found"}), 404

    device_data = {
        "device_id": device.device_id,
        "user_id": device.user_id,
        "plant_id": device.plant_id,
        "device_name": device.device_name,
        "started_at": device.started_at.isoformat()
    }
    return jsonify(device_data), 200


@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.get_json()
    device = Device.query.get(device_id)

    if not device:
        return jsonify({"msg": "Device not found"}), 404

    device_name = data.get('device_name')
    plant_id = data.get('plant_id')

    if device_name:
        device.device_name = device_name

    if plant_id:
        device.plant_id = plant_id

    db.session.commit()
    return jsonify({"msg": "Device updated successfully"}), 200


@app.route('/api/sensor-data/day/<int:device_id>', methods=['GET'])
def get_sensor_data_day(device_id):
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)

    sensor_data = SensorData.query.filter(
        SensorData.device_id == device_id,
        SensorData.timestamp >= start_time,
        SensorData.timestamp <= end_time
    ).order_by(SensorData.timestamp.asc()).all()

    if not sensor_data:
        return jsonify({"msg": "No sensor data found for the last 24 hours"}), 404

    data = []
    for entry in sensor_data:
        data.append({
            "data_id": entry.data_id,
            "device_id": entry.device_id,
            "timestamp": entry.timestamp.isoformat(),
            "soil_moisture_level": entry.soil_moisture_level,
            "temperature": entry.temperature,
            "humidity": entry.humidity,
            "water_level": entry.water_level
        })

    return jsonify(data), 200


@app.route('/api/sensor-data/week/<int:device_id>', methods=['GET'])
def get_sensor_data_week(device_id):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    sensor_data = SensorData.query.filter(
        SensorData.device_id == device_id,
        SensorData.timestamp >= start_time,
        SensorData.timestamp <= end_time,
        # Filtering for entries at the start of each hour
        db.extract('minute', SensorData.timestamp) == 0
    ).order_by(SensorData.timestamp.asc()).all()

    if not sensor_data:
        return jsonify({"msg": "No sensor data found for the past month"}), 404

    data = []
    for entry in sensor_data:
        data.append({
            "data_id": entry.data_id,
            "device_id": entry.device_id,
            "timestamp": entry.timestamp.isoformat(),
            "soil_moisture_level": entry.soil_moisture_level,
            "temperature": entry.temperature,
            "humidity": entry.humidity,
            "water_level": entry.water_level
        })

    return jsonify(data), 200


@app.route('/api/sensor-data/month/<int:device_id>', methods=['GET'])
def get_sensor_data_month(device_id):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)

    sensor_data = SensorData.query.filter(
        SensorData.device_id == device_id,
        SensorData.timestamp >= start_time,
        SensorData.timestamp <= end_time,
        db.extract('minute', SensorData.timestamp) == 0,
        db.extract('hour', SensorData.timestamp).in_(
            [0, 6, 12, 18])
    ).order_by(SensorData.timestamp.asc()).all()

    if not sensor_data:
        return jsonify({"msg": "No sensor data found for the past month"}), 404

    data = []
    for entry in sensor_data:
        data.append({
            "data_id": entry.data_id,
            "device_id": entry.device_id,
            "timestamp": entry.timestamp.isoformat(),
            "soil_moisture_level": entry.soil_moisture_level,
            "temperature": entry.temperature,
            "humidity": entry.humidity,
            "water_level": entry.water_level
        })

    return jsonify(data), 200


@app.route('/api/sensor-data/<int:device_id>', methods=['POST'])
def store_sensor_data(device_id):
    data = request.get_json()
    timestamp = datetime.now()
    soil_moisture_level = data.get('soil_moisture_level')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    water_level = data.get('water_level')

    if soil_moisture_level is None or temperature is None or humidity is None or water_level is None:
        return jsonify({"msg": "Missing sensor data"}), 400

    new_sensor_data = SensorData(
        device_id=device_id,
        timestamp=timestamp,
        soil_moisture_level=soil_moisture_level,
        temperature=temperature,
        humidity=humidity,
        water_level=water_level
    )

    db.session.add(new_sensor_data)
    db.session.commit()

    return jsonify({"msg": "Sensor data stored successfully"}), 200


@app.route('/api/commands/<int:device_id>', methods=['POST'])
def issue_command(device_id):
    data = request.get_json()
    command_body = data.get('command_body')
    # Default status is 'pending'
    command_status = data.get('command_status', 'pending')
    issued_at = datetime.now()

    if not command_body:
        return jsonify({"msg": "Missing command_body"}), 400

    new_command = Command(
        device_id=device_id,
        command_body=command_body,
        command_status=command_status,
        issued_at=issued_at
    )

    db.session.add(new_command)
    db.session.commit()

    return jsonify({"msg": "Command issued successfully", "command_id": new_command.command_id}), 200


@app.route('/api/commands/<int:device_id>', methods=['GET'])
def get_recent_commands(device_id):
    one_hour_ago = datetime.now() - timedelta(hours=1)

    recent_command = Command.query.filter(
        Command.device_id == device_id,
        Command.issued_at >= one_hour_ago,
        Command.command_status == "pending"
    ).order_by(Command.issued_at.desc()).first()

    if not recent_command:
        return jsonify({"msg": "No commands found for the last hour"}), 404

    # commands_data = []
    # for command in recent_commands:
    #     commands_data.append({
    #         "command_id": command.command_id,
    #         "device_id": command.device_id,
    #         "command_body": command.command_body,
    #         "command_status": command.command_status,
    #         "issued_at": command.issued_at.isoformat()
    #     })
    command_data = {
        "command_id": recent_command.command_id,
        "device_id": recent_command.device_id,
        "command_body": recent_command.command_body,
        "command_status": recent_command.command_status,
        "issued_at": recent_command.issued_at.isoformat()
    }   

    return jsonify(command_data), 200


# have to push the larger delays next time
@app.route('/api/commands/ack/<int:command_id>', methods=['POST'])
def acknowledge_command(command_id):
    command = Command.query.get(command_id)

    if not command:
        return jsonify({"msg": "Command not found"}), 404

    command.command_status = "complete"
    db.session.commit()

    return jsonify({"msg": "Command status set to complete"}), 200


@app.route('/api/device-status/learning-mode/<int:device_id>', methods=['POST'])
def learning_mode(device_id):
    print(f"Learning mode for device {device_id}")
    data = request.get_json()
    if "isLearning" not in data:
        return jsonify({"msg": "Missing isLearning"}), 400
    
    isLearning = data.get('isLearning')

    if isLearning:
        device_status = DeviceStatus.query.filter_by(device_id=device_id).first()

        if not device_status:
            return jsonify({"msg": "Device status not found"}), 404

        device_status.watering_mode = "Learning"
        device_status.watering_amount = 100
        device_status.watering_frequency = timedelta(minutes=2)

        command_body = {
            "commandType": "SetLearningWatering",
            "amount": 100,
        }
        new_command = Command(
        device_id=device_id,
        command_body=command_body,
        command_status="pending",
        issued_at=datetime.now()
        )
        db.session.add(new_command)
        db.session.commit()
        
        start_moisture = SensorData.query.order_by(SensorData.timestamp.desc()).first().soil_moisture_level

        run_time = datetime.now() + timedelta(minutes=10)
        scheduler.add_job(
            id=f"learning_mode_initialize_{device_id}_{run_time}",
            func=learning_mode_initialize,
            trigger="date",
            run_date=run_time,
            args=[device_id, start_moisture, 100] 
        )

    return jsonify({"msg": "Device status updated successfully"}), 200

def learning_mode_initialize(device_id, start_moisture, water_amount):
    with app.app_context():
        print(f"Learning mode initialized for device {device_id} {start_moisture} {water_amount}")
        current_moisture = SensorData.query.order_by(SensorData.timestamp.desc()).first().soil_moisture_level

        run_time = datetime.now() + timedelta(minutes=9*60 + 50) # 9 hours and 50 minutes
        scheduler.add_job(
            id=f"learning_mode_analyze_{device_id}_{run_time}",
            func=learning_mode_analyze,
            trigger="date",
            run_date=run_time,
            args=[device_id, start_moisture, current_moisture, water_amount]
        )

        return jsonify({"msg": "Learning mode initialized"}), 200


def learning_mode_analyze(device_id, start_moisture, watered_moisture, water_amount):
    with app.app_context():
        print(f"Learning mode analyze for device {device_id} {start_moisture} {watered_moisture} {water_amount}")
        TARGET_MOISTURE_DIFF = 0.4
        plant_name = DeviceStatus.query.filter_by(device_id=device_id).first().plant_name
        TARGET_MOISTURE = Plant.query.filter_by(species_name=plant_name).first().plant_moisture_level
        current_moisture = SensorData.query.order_by(SensorData.timestamp.desc()).first().soil_moisture_level

        watering_moisture_diff = watered_moisture - start_moisture
        waiting_moisture_diff = watered_moisture - current_moisture

        # scale new water amount to reach target watering moisture difference, convert to int
        new_water_amount = round(float(TARGET_MOISTURE_DIFF)/float(watering_moisture_diff) * float(water_amount))
        new_waiting_time = timedelta(minutes=round(float(TARGET_MOISTURE_DIFF)/float(waiting_moisture_diff) * (10*60)))

        # start moisture
        desired_moisture = TARGET_MOISTURE - TARGET_MOISTURE_DIFF/2

        # current moisture is higher than desired moisture, just need to wait
        if current_moisture > desired_moisture:
            while current_moisture < desired_moisture:
                current_moisture = SensorData.query.order_by(SensorData.timestamp.desc()).first().soil_moisture_level
                # wait 10 minutes
                print(f"Waiting for moisture to drop to {desired_moisture}")
                time.sleep(600)
        # current moisture is lower than desired moisture, need to water
        else:
            adjustment_moisture_diff = desired_moisture - current_moisture
            # scale new water amount to reach target watering moisture difference, convert to int
            adjustment_water_amount = round(float(adjustment_moisture_diff)/float(TARGET_MOISTURE_DIFF) * float(new_water_amount))
            command_body = {
                "commandType": "SetManualWaterAmount",
                "amount": adjustment_water_amount,
            }
            new_command = Command(
                device_id=device_id,
                command_body=command_body,
                command_status="pending",
            )
            db.session.add(new_command)
            db.session.commit()
            # wait 2 minutes for commmand to run
            time.sleep(120)
        
        # update device status to auto mode
        device_status = DeviceStatus.query.filter_by(device_id=device_id).first()
        device_status.watering_amount = new_water_amount
        device_status.watering_frequency = new_waiting_time
        device_status.watering_mode = "Automatic"

        db.session.commit()


@app.route('/api/device-status/<int:device_id>', methods=['GET'])
def get_device_status(device_id):
    device_status = DeviceStatus.query.filter_by(device_id=device_id).first()

    if not device_status:
        return jsonify({"msg": "Device status not found"}), 404

    status_data = {
        "device_id": device_status.device_id,
        "target_temperature": device_status.target_temperature,
        "watering_mode": device_status.watering_mode,
        "heating_mode": device_status.heating_mode,
        "water_level": device_status.water_level,
        "heater_status": device_status.heater_status,
        "vent_status": device_status.vent_status,
        "plant_name": device_status.plant_name,
        "watering_amount": device_status.watering_amount,
        "watering_frequency": device_status.watering_frequency.total_seconds() // 3600  # Convert to hours
    }

    return jsonify(status_data), 200


@app.route('/api/device-status/<int:device_id>', methods=['POST'])
def update_device_status(device_id):
    data = request.get_json()
    device_status = DeviceStatus.query.filter_by(device_id=device_id).first()

    if not device_status:
        return jsonify({"msg": "Device status not found"}), 404

    if 'target_temperature' in data:
        device_status.target_temperature = data['target_temperature']
    if 'watering_mode' in data:
        device_status.watering_mode = data['watering_mode']
    if 'heating_mode' in data:
        device_status.heating_mode = data['heating_mode']
    if 'water_level' in data:
        device_status.water_level = data['water_level']
    if 'heater_status' in data:
        device_status.heater_status = data['heater_status']
    if 'vent_status' in data:
        device_status.vent_status = data['vent_status']
    if 'plant_name' in data:
        device_status.plant_name = data['plant_name']
    if 'watering_amount' in data:
        device_status.watering_amount = data['watering_amount']
    if 'watering_frequency' in data:
        device_status.watering_frequency = timedelta(hours=data['watering_frequency'])

    db.session.commit()

    return jsonify({"msg": "Device status updated successfully"}), 200

@app.route('/api/plants', methods=['GET'])
def get_plants():
    plants = Plant.query.all()

    if not plants:
        return jsonify({"msg": "No plant species found"}), 404

    plant_data = []
    for plant in plants:
        plant_data.append({
            "plant_id": plant.plant_id,
            "species_name": plant.species_name,
            "min_temp_range": plant.min_temp_range,
            "max_temp_range": plant.max_temp_range,
            "watering_frequency": plant.watering_frequency.total_seconds() // 3600,  # Convert to hours
            "watering_amount": plant.watering_amount,
            "plant_moisture_level": plant.plant_moisture_level
        })

    return jsonify(plant_data), 200


@app.route('/api/plants/<int:plant_id>', methods=['GET'])
def get_plant(plant_id):
    plant = Plant.query.get(plant_id)

    if not plant:
        return jsonify({"msg": "Plant species not found"}), 404

    plant_data = {
        "plant_id": plant.plant_id,
        "species_name": plant.species_name,
        "min_temp_range": plant.min_temp_range,
        "max_temp_range": plant.max_temp_range,
        "watering_frequency": plant.watering_frequency.total_seconds() // 3600,  # Convert to hours
        "watering_amount": plant.watering_amount,
        "plant_moisture_level": plant.plant_moisture_level
    }

    return jsonify(plant_data), 200

if __name__ == '__main__':
    print("Startup started")
    app.run(debug=True, host='0.0.0.0', port=5000)

