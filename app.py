from flask import Flask, render_template, request, redirect, url_for
from database import db_uri, Customer, Facility, Building, Meter, GenerationSource, process_load_data, process_generation_data
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
    return render_template('index.html')

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
        source_id = int(request.form['source_id'])
        file = request.files['file']

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
    session.close()
    return render_template('upload.html', meters=meters, generation_sources=generation_sources)

if __name__ == '__main__':
    if not os.path.exists(db_uri.split('///')[1]):
        from database import create_database
        create_database()
    app.run(debug=True)
