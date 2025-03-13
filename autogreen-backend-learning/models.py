from flask import Flask
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy

# look into flask-migrate if we need to change the models/database tables
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


class Plant(db.Model):
    __tablename__ = 'plants'
    plant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    species_name = db.Column(db.String, nullable=False)
    min_temp_range = db.Column(db.Integer, nullable=False)
    max_temp_range = db.Column(db.Integer, nullable=False)
    watering_frequency = db.Column(db.Interval, nullable=False)
    watering_amount = db.Column(db.Integer, nullable=False)
    plant_moisture_level = db.Column(db.Integer, nullable=False)


class Device(db.Model):
    __tablename__ = 'devices'
    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.user_id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey(
        'plants.plant_id'), nullable=False)
    device_name = db.Column(db.String, nullable=False)
    started_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref=db.backref('devices', lazy=True))
    plant = db.relationship('Plant', backref=db.backref('devices', lazy=True))


class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    data_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey(
        'devices.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(
        timezone.utc), nullable=False)
    soil_moisture_level = db.Column(db.Numeric, nullable=False)
    temperature = db.Column(db.Numeric, nullable=False)
    humidity = db.Column(db.Numeric, nullable=False)
    water_level = db.Column(db.Numeric, nullable=False)

    device = db.relationship(
        'Device', backref=db.backref('sensor_data', lazy=True))


class DeviceStatus(db.Model):
    __tablename__ = 'device_status'
    device_id = db.Column(db.Integer, db.ForeignKey(
        'devices.device_id'), primary_key=True)
    target_temperature = db.Column(db.Numeric, nullable=False)
    watering_mode = db.Column(db.String, nullable=False)
    heating_mode = db.Column(db.String, nullable=False)
    water_level = db.Column(db.Numeric, nullable=False)
    heater_status = db.Column(db.String, nullable=False)
    vent_status = db.Column(db.String, nullable=False)
    plant_name = db.Column(db.String, nullable=True)
    watering_amount = db.Column(db.Integer, nullable=True)
    watering_frequency = db.Column(db.Interval, nullable=True)

    device = db.relationship('Device', backref=db.backref('device_status', lazy=True))

class Command(db.Model):
    __tablename__ = 'commands'
    command_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey(
        'devices.device_id'), nullable=False)
    command_body = db.Column(db.JSON, nullable=False)
    command_status = db.Column(db.String, default="waiting", nullable=False)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(
        timezone.utc), nullable=False)

    device = db.relationship(
        'Device', backref=db.backref('commands', lazy=True))
