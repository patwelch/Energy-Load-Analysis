from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import db_uri, Customer, Facility, Building, Meter, GenerationSource, LoadData, GenerationData, process_load_data, process_generation_data
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

app = Flask(__name__)

# Database setup
engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)

@app.teardown_appcontext
def shutdown_session(exception=None):
    # In a real app, you would manage the session more carefully
    pass

@app.route('/')
def index():
    session = Session()
    meters = session.query(Meter).all()
    generation_sources = session.query(GenerationSource).all()
    session.close()
    return render_template('index.html', meters=meters, generation_sources=generation_sources)

@app.route('/sources')
def sources():
    session = Session()
    customers = session.query(Customer).all()
    generation_sources = session.query(GenerationSource).all()
    session.close()
    return render_template('sources.html', customers=customers, generation_sources=generation_sources)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    session = Session()
    if request.method == 'POST':
        source_type = request.form['source_type']
        file = request.files['file']

        if 'new_source_checkbox' in request.form:
            if source_type == 'load':
                new_meter_name = request.form['new_meter_name']
                building_id = int(request.form['building_id'])
                new_meter = Meter(name=new_meter_name, building_id=building_id)
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
            temp_path = os.path.join('database', file.filename)
            file.save(temp_path)

            if source_type == 'load':
                process_load_data(session, temp_path, source_id)
            elif source_type == 'generation':
                process_generation_data(session, temp_path, source_id)

            os.remove(temp_path)

            session.close()
            return redirect(url_for('upload'))

    meters = session.query(Meter).all()
    generation_sources = session.query(GenerationSource).all()
    buildings = session.query(Building).all()
    session.close()
    return render_template('upload.html', meters=meters, generation_sources=generation_sources, buildings=buildings)

@app.route('/api/data')
def get_data():
    meter_id = request.args.get('meter_id', type=int)
    generation_ids = request.args.getlist('generation_ids[]', type=int)

    session = Session()

    # Fetch load data
    load_query = session.query(LoadData.timestamp, LoadData.load_mw).filter(LoadData.meter_id == meter_id)
    load_data = {ts.isoformat(): l for ts, l in load_query.all()}

    # Fetch generation data
    generation_data = {}
    for gen_id in generation_ids:
        gen_query = session.query(GenerationData.timestamp, GenerationData.generation_mw).filter(GenerationData.source_id == gen_id)
        for ts, gen_mw in gen_query.all():
            ts_iso = ts.isoformat()
            if ts_iso not in generation_data:
                generation_data[ts_iso] = 0
            generation_data[ts_iso] += gen_mw

    session.close()

    return jsonify({
        'load': load_data,
        'generation': generation_data
    })

if __name__ == '__main__':
    if not os.path.exists(db_uri.split('///')[1]):
        from database import create_database
        create_database()
    app.run(debug=True)
