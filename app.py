from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class Airline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    delays = db.relationship('DelayRecord', backref='airline', lazy=True)

class Airport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=True)
    delays = db.relationship('DelayRecord', backref='airport', lazy=True)

class DelayRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airline.id'), nullable=False)
    airport_id = db.Column(db.Integer, db.ForeignKey('airport.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    arr_flights = db.Column(db.Integer, default=0)
    arr_del15 = db.Column(db.Integer, default=0)
    carrier_delay = db.Column(db.Float, default=0.0)
    weather_delay = db.Column(db.Float, default=0.0)
    nas_delay = db.Column(db.Float, default=0.0)
    security_delay = db.Column(db.Float, default=0.0)
    late_aircraft_delay = db.Column(db.Float, default=0.0)

# --- ROUTES ---
@app.route('/')
def index():
    # Automatically redirect the root URL to the manage page
    return redirect(url_for('manage'))

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':
        new_record = DelayRecord(
            airline_id=request.form['airline_id'],
            airport_id=request.form['airport_id'],
            year=int(request.form['year']),
            month=int(request.form['month']),
            arr_flights=float(request.form['arr_flights']),
            carrier_delay=float(request.form['carrier_delay'])
        )
        db.session.add(new_record)
        db.session.commit()
        return redirect(url_for('manage'))

    airlines = Airline.query.order_by(Airline.name).all()
    airports = Airport.query.order_by(Airport.name).all()
    recent_records = DelayRecord.query.order_by(DelayRecord.id.desc()).limit(15).all()
    
    return render_template('manage.html', airlines=airlines, airports=airports, records=recent_records)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):
    record = DelayRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('manage'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_record(id):
    record = DelayRecord.query.get_or_404(id)
    if request.method == 'POST':
        record.year = int(request.form['year'])
        record.month = int(request.form['month'])
        record.arr_flights = float(request.form['arr_flights'])
        record.carrier_delay = float(request.form['carrier_delay'])
        db.session.commit()
        return redirect(url_for('manage'))
        
    return render_template('edit.html', record=record)

@app.route('/report', methods=['GET', 'POST'])
def report():
    airlines = Airline.query.order_by(Airline.name).all()
    airports = Airport.query.order_by(Airport.name).all()
    
    report_data = None
    
    if request.method == 'POST':
        airport_id = request.form.get('airport_id')
        airline_id = request.form.get('airline_id')
        start_year = request.form.get('start_year', type=int)
        end_year = request.form.get('end_year', type=int)
        
        query = DelayRecord.query
        
        # Apply filters
        if airport_id: query = query.filter_by(airport_id=airport_id)
        if airline_id: query = query.filter_by(airline_id=airline_id)
        if start_year: query = query.filter(DelayRecord.year >= start_year)
        if end_year: query = query.filter(DelayRecord.year <= end_year)
            
        records = query.all()
        
        if records:
            total_flights = sum(r.arr_flights for r in records)
            total_delays = sum(r.arr_del15 for r in records)
            
            # Fetch names for the UI display
            selected_airport = Airport.query.get(airport_id).name if airport_id else "All Airports"
            selected_airline = Airline.query.get(airline_id).name if airline_id else "All Airlines"
            
            # Aggregate totals for the Donut Chart
            chart_data = [
                sum(r.carrier_delay for r in records),
                sum(r.weather_delay for r in records),
                sum(r.nas_delay for r in records),
                sum(r.security_delay for r in records),
                sum(r.late_aircraft_delay for r in records)
            ]
            
            report_data = {
                'filter_airport': selected_airport,
                'filter_airline': selected_airline,
                'start_year': start_year or "Any",
                'end_year': end_year or "Any",
                'total_flights': int(total_flights),
                'delay_probability': round((total_delays / total_flights * 100) if total_flights > 0 else 0, 2),
                'avg_carrier_delay': round(sum(r.carrier_delay for r in records) / len(records), 2),
                'avg_weather_delay': round(sum(r.weather_delay for r in records) / len(records), 2),
                'chart_data': chart_data,
                'records': records  # <--- THIS IS THE MISSING PIECE!
            }
        else:
            report_data = {'error': 'No records found for this combination.'}
            
    return render_template('report.html', airlines=airlines, airports=airports, report_data=report_data)

@app.route('/api/airlines_for_airport/<int:airport_id>')
def airlines_for_airport(airport_id):
    # Find distinct airlines that have delay records at this airport
    records = DelayRecord.query.filter_by(airport_id=airport_id).all()
    airline_ids = list(set(r.airline_id for r in records))
    airlines = Airline.query.filter(Airline.id.in_(airline_ids)).order_by(Airline.name).all()
    
    return jsonify([{'id': a.id, 'name': a.name, 'iata_code': a.iata_code} for a in airlines])

@app.route('/api/airports_for_airline/<int:airline_id>')
def airports_for_airline(airline_id):
    # Find distinct airports that this airline has records for
    records = DelayRecord.query.filter_by(airline_id=airline_id).all()
    airport_ids = list(set(r.airport_id for r in records))
    airports = Airport.query.filter(Airport.id.in_(airport_ids)).order_by(Airport.name).all()
    
    return jsonify([{'id': a.id, 'name': a.name, 'iata_code': a.iata_code} for a in airports])

if __name__ == '__main__':
    app.run(debug=True)