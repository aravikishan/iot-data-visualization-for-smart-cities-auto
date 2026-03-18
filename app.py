from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from datetime import datetime
import sqlite3
import os

app = FastAPI()

# Set up templates and static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
DATABASE = 'iot_data.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            location TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER,
            value REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sensor_id) REFERENCES sensors(id)
        )
    ''')
    # Seed data
    cursor.execute("INSERT INTO sensors (type, location, value) VALUES ('Temperature', 'Downtown', 23.5)")
    cursor.execute("INSERT INTO sensors (type, location, value) VALUES ('Humidity', 'Uptown', 45.0)")
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class Sensor(BaseModel):
    id: int
    type: str
    location: str
    value: float
    timestamp: datetime

class HistoricalData(BaseModel):
    sensor_id: int
    value: float
    timestamp: datetime

# API Endpoints
@app.get("/api/sensors", response_model=List[Sensor])
async def get_sensors():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensors")
    sensors = cursor.fetchall()
    conn.close()
    return [Sensor(id=row[0], type=row[1], location=row[2], value=row[3], timestamp=row[4]) for row in sensors]

@app.get("/api/sensors/{sensor_id}", response_model=Sensor)
async def get_sensor(sensor_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensors WHERE id = ?", (sensor_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Sensor(id=row[0], type=row[1], location=row[2], value=row[3], timestamp=row[4])
    raise HTTPException(status_code=404, detail="Sensor not found")

@app.post("/api/sensors", response_model=Sensor)
async def add_sensor(sensor: Sensor):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sensors (type, location, value) VALUES (?, ?, ?)", (sensor.type, sensor.location, sensor.value))
    conn.commit()
    sensor_id = cursor.lastrowid
    conn.close()
    return {**sensor.dict(), "id": sensor_id}

@app.put("/api/sensors/{sensor_id}", response_model=Sensor)
async def update_sensor(sensor_id: int, sensor: Sensor):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE sensors SET type = ?, location = ?, value = ? WHERE id = ?", (sensor.type, sensor.location, sensor.value, sensor_id))
    conn.commit()
    conn.close()
    return {**sensor.dict(), "id": sensor_id}

@app.delete("/api/sensors/{sensor_id}")
async def delete_sensor(sensor_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
    conn.commit()
    conn.close()
    return {"detail": "Sensor deleted"}

# HTML Endpoints
@app.get("/", response_class=HTMLResponse)
async def dashboard(request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/sensors", response_class=HTMLResponse)
async def sensors_page(request):
    return templates.TemplateResponse("sensors.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request):
    return templates.TemplateResponse("about.html", {"request": request})
