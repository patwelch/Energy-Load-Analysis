
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
import os

# Define the base class for declarative models
Base = declarative_base()

# Define the database file path
db_path = os.path.join('database', 'database.db')
db_uri = f'sqlite:///{db_path}'

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    facilities = relationship("Facility", back_populates="customer")

class Facility(Base):
    __tablename__ = 'facilities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="facilities")
    buildings = relationship("Building", back_populates="facility")

class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    facility = relationship("Facility", back_populates="buildings")
    meters = relationship("Meter", back_populates="building")

class Meter(Base):
    __tablename__ = 'meters'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id'))
    building = relationship("Building", back_populates="meters")
    load_data = relationship("LoadData", back_populates="meter")

class LoadData(Base):
    __tablename__ = 'load_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    load_mw = Column(Float, nullable=False)
    meter_id = Column(Integer, ForeignKey('meters.id'))
    meter = relationship("Meter", back_populates="load_data")
    __table_args__ = (UniqueConstraint('timestamp', 'meter_id', name='_timestamp_meter_uc'),)

class GenerationSource(Base):
    __tablename__ = 'generation_sources'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String)
    generation_data = relationship("GenerationData", back_populates="source")

class GenerationData(Base):
    __tablename__ = 'generation_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    generation_mw = Column(Float, nullable=False)
    source_id = Column(Integer, ForeignKey('generation_sources.id'))
    source = relationship("GenerationSource", back_populates="generation_data")
    __table_args__ = (UniqueConstraint('timestamp', 'source_id', name='_timestamp_source_uc'),)

import csv
from datetime import datetime
from sqlalchemy.exc import IntegrityError

def create_database():
    """Creates the database and all tables."""
    # Ensure the database directory exists
    if not os.path.exists('database'):
        os.makedirs('database')
    
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    print(f"Database created at {db_path}")

def process_load_data(session, file_path, meter_id):
    """Processes an uploaded load data file and inserts data into the database."""
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for i, row in enumerate(reader):
            if len(row) != 2:
                raise ValueError(f"Row {i+2} has an incorrect number of columns.")
            try:
                timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                if timestamp.minute != 0 or timestamp.second != 0:
                    raise ValueError(f"Timestamp in row {i+2} is not in hourly increments.")
                load_mw = float(row[1])
            except ValueError as e:
                raise ValueError(f"Invalid data in row {i+2}: {e}")

            load_data = LoadData(timestamp=timestamp, load_mw=load_mw, meter_id=meter_id)
            session.add(load_data)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ValueError("Data with this timestamp and meter already exists.")

def process_generation_data(session, file_path, source_id):
    """Processes an uploaded generation data file and inserts data into the database."""
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for i, row in enumerate(reader):
            if len(row) != 2:
                raise ValueError(f"Row {i+2} has an incorrect number of columns.")
            try:
                timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                if timestamp.minute != 0 or timestamp.second != 0:
                    raise ValueError(f"Timestamp in row {i+2} is not in hourly increments.")
                generation_mw = float(row[1])
            except ValueError as e:
                raise ValueError(f"Invalid data in row {i+2}: {e}")

            generation_data = GenerationData(timestamp=timestamp, generation_mw=generation_mw, source_id=source_id)
            session.add(generation_data)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ValueError("Data with this timestamp and source already exists.")

if __name__ == '__main__':
    create_database()
