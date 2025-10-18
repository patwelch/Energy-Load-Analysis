from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import db_uri, Customer, Facility, Building, Meter, GenerationSource, LoadData, GenerationData, process_load_data, process_generation_data, get_aggregated_load_data, get_aggregated_generation_data, get_monthly_avg_generation_data, get_monthly_avg_load_data
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('app.log'),
                        logging.StreamHandler()
                    ])

app = Flask(__name__)

# Database setup
engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error('An error occurred: %s', e, exc_info=True)
    return jsonify(error=str(e)), 500

@app.teardown_appcontext
def shutdown_session(exception=None):
    # In a real app, you would manage the session more carefully
    pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    session = Session()
    meters = session.query(Meter).all()
    generation_sources = session.query(GenerationSource).all()
    session.close()
    return render_template('dashboard.html', meters=meters, generation_sources=generation_sources)



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    session = Session()
    if request.method == 'POST':
        app.logger.info('Processing file upload')
        source_type = request.form['source_type']
        file = request.files['file']

        if 'new_source_checkbox' in request.form:
            if source_type == 'load':
                new_meter_name = request.form['new_meter_name']
                new_meter = Meter(name=new_meter_name)
                session.add(new_meter)
                session.commit()
                source_id = new_meter.id
            elif source_type == 'generation':
                new_generation_source_name = request.form['new_generation_source_name']
                generation_source_type = request.form['generation_source_type']
                new_source = GenerationSource(name=new_generation_source_name, type=generation_source_type)
                session.add(new_source)
                session.commit()
                source_id = new_source.id
        else:
            source_id = int(request.form['source_id'])

        if file:
            if source_type == 'load':
                process_load_data(session, file.stream, source_id)
            elif source_type == 'generation':
                process_generation_data(session, file.stream, source_id)

            session.close()
            return redirect(url_for('upload'))

    meters = session.query(Meter).all()
    generation_sources = session.query(GenerationSource).all()
    session.close()
    return render_template('upload.html', meters=meters, generation_sources=generation_sources)

@app.route('/api/generation_sources')
def get_generation_sources():
    session = Session()
    generation_sources = session.query(GenerationSource).all()
    session.close()
    return jsonify([{'id': source.id, 'name': source.name} for source in generation_sources])

@app.route('/api/data')
def get_data():
    meter_ids = request.args.getlist('meter_ids[]', type=int)
    generation_ids = request.args.getlist('generation_ids[]', type=int)

    session = Session()
    try:
        # Fetch and format load data
        load_data_tuples = get_monthly_avg_load_data(session, meter_ids)
        load_data = {f"{month}-{hour}": l for month, hour, l in load_data_tuples}

        # Fetch and format generation data
        generation_data_tuples = get_monthly_avg_generation_data(session, generation_ids)
        generation_data_agg = {}
        for month, hour, name, gen_mw in generation_data_tuples:
            key = f"{month}-{hour}"
            if key not in generation_data_agg:
                generation_data_agg[key] = {}
            generation_data_agg[key][name] = gen_mw

    finally:
        session.close()

    return jsonify({
        'load': load_data,
        'generation': generation_data_agg
    })
