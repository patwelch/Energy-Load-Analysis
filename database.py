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
    building_id = Column(Integer, ForeignKey('buildings.id'), nullable=True)
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



def process_load_data(session, file, meter_id):
    """Processes an uploaded load data file and inserts data into the database."""
    reader = csv.reader(file)
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

def process_generation_data(session, file, source_id):
    """Processes an uploaded generation data file and inserts data into the database."""
    reader = csv.reader(file)
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

def get_aggregated_load_data(session, meter_ids, start_date, end_date):
    """Aggregates load data for the given meters and date range."""
    return session.query(
        LoadData.timestamp,
        sqlalchemy.func.sum(LoadData.load_mw).label('total_load_mw')
    ).filter(
        LoadData.meter_id.in_(meter_ids),
        LoadData.timestamp.between(start_date, end_date)
    ).group_by(LoadData.timestamp).order_by(LoadData.timestamp).all()

def get_aggregated_generation_data(session, source_ids, start_date, end_date):
    """Aggregates generation data for the given sources and date range."""
    return session.query(
        GenerationData.timestamp,
        GenerationSource.name,
        sqlalchemy.func.sum(GenerationData.generation_mw).label('total_generation_mw')
    ).join(GenerationSource).filter(
        GenerationData.source_id.in_(source_ids),
        GenerationData.timestamp.between(start_date, end_date)
    ).group_by(GenerationData.timestamp, GenerationSource.name).order_by(GenerationData.timestamp).all()
    
def get_monthly_avg_load_data(session, meter_ids):
    """
    Aggregates load data, averaging each hour of each month over the last 3 years of data.
    """
    if not meter_ids:
        return []

    max_year_result = session.query(sqlalchemy.func.max(sqlalchemy.func.strftime('%Y', LoadData.timestamp))).scalar()
    if not max_year_result:
        return []

    max_year = int(max_year_result)
    three_years_ago = str(max_year - 2)

    # SQLite specific strftime: '%m' is month (01-12), '%H' is hour (00-23)
    month_of_year = sqlalchemy.func.strftime('%m', LoadData.timestamp)
    hour_of_day = sqlalchemy.func.strftime('%H', LoadData.timestamp)

    return session.query(
        month_of_year.label('month'),
        hour_of_day.label('hour'),
        sqlalchemy.func.avg(LoadData.load_mw).label('avg_load_mw')
    ).filter(
        LoadData.meter_id.in_(meter_ids),
        sqlalchemy.func.strftime('%Y', LoadData.timestamp) >= three_years_ago
    ).group_by('month', 'hour').order_by('month', 'hour').all()

def get_monthly_avg_generation_data(session, source_ids):
    """
    Aggregates generation data, averaging each hour of each month over the last 3 years of data.
    """
    if not source_ids:
        return []

    max_year_result = session.query(sqlalchemy.func.max(sqlalchemy.func.strftime('%Y', GenerationData.timestamp))).scalar()
    if not max_year_result:
        return []

    max_year = int(max_year_result)
    three_years_ago = str(max_year - 2)

    month_of_year = sqlalchemy.func.strftime('%m', GenerationData.timestamp)
    hour_of_day = sqlalchemy.func.strftime('%H', GenerationData.timestamp)

    return session.query(
        month_of_year.label('month'),
        hour_of_day.label('hour'),
        GenerationSource.name,
        sqlalchemy.func.avg(GenerationData.generation_mw).label('avg_generation_mw')
    ).join(GenerationSource).filter(
        GenerationData.source_id.in_(source_ids),
        sqlalchemy.func.strftime('%Y', GenerationData.timestamp) >= three_years_ago
    ).group_by('month', 'hour', GenerationSource.name).order_by('month', 'hour').all()


def get_yearly_avg_load_data(session, meter_ids):
    """
    DEPRECATED: Aggregates load data, averaging each hour of the year over the last 3 years of data.
    """
    if not meter_ids: return []
    max_year_result = session.query(sqlalchemy.func.max(sqlalchemy.func.strftime('%Y', LoadData.timestamp))).scalar()
    if not max_year_result: return []
    max_year = int(max_year_result)
    three_years_ago = str(max_year - 2)
    hour_of_year = (sqlalchemy.func.strftime('%j', LoadData.timestamp) - 1) * 24 + sqlalchemy.func.strftime('%H', LoadData.timestamp)
    return session.query(hour_of_year.label('hour_of_year'), sqlalchemy.func.avg(LoadData.load_mw).label('avg_load_mw')).filter(LoadData.meter_id.in_(meter_ids), sqlalchemy.func.strftime('%Y', LoadData.timestamp) >= three_years_ago).group_by('hour_of_year').order_by('hour_of_year').all()

def get_yearly_avg_generation_data(session, source_ids):
    """
    DEPRECATED: Aggregates generation data, averaging each hour of the year over the last 3 years of data.
    """
    if not source_ids: return []
    max_year_result = session.query(sqlalchemy.func.max(sqlalchemy.func.strftime('%Y', GenerationData.timestamp))).scalar()
    if not max_year_result: return []
    max_year = int(max_year_result)
    three_years_ago = str(max_year - 2)
    hour_of_year = (sqlalchemy.func.strftime('%j', GenerationData.timestamp) - 1) * 24 + sqlalchemy.func.strftime('%H', GenerationData.timestamp)
    return session.query(hour_of_year.label('hour_of_year'), GenerationSource.name, sqlalchemy.func.avg(GenerationData.generation_mw).label('avg_generation_mw')).join(GenerationSource).filter(GenerationData.source_id.in_(source_ids), sqlalchemy.func.strftime('%Y', GenerationData.timestamp) >= three_years_ago).group_by('hour_of_year', GenerationSource.name).order_by('hour_of_year').all()