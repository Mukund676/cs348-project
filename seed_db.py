import csv
from app import app, db, Airline, Airport, DelayRecord

def seed():
    with app.app_context():
        # Clear existing data and recreate tables
        db.drop_all()
        db.create_all()

        print("Loading Airports...")
        valid_airports = {}
        with open('airports.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter for large airports with a valid IATA code
                if row['type'] == 'large_airport' and row['iata_code'] and row['iata_code'] != '\\N':
                    airport = Airport(iata_code=row['iata_code'], name=row['name'], city=row['municipality'])
                    db.session.add(airport)
                    valid_airports[row['iata_code']] = airport
        db.session.commit()
        print(f"Inserted {len(valid_airports)} large airports.")

        print("Loading Airlines...")
        valid_airlines = {}
        with open('airlines.csv', encoding='iso-8859-1') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter for active airlines with a valid IATA code
                if row['Active'] == 'Y' and row['IATA'] and row['IATA'] != '\\N' and row['IATA'] != '-':
                    # Prevent duplicates if dataset has them
                    if row['IATA'] not in valid_airlines:
                        airline = Airline(iata_code=row['IATA'], name=row['Name'])
                        db.session.add(airline)
                        valid_airlines[row['IATA']] = airline
        db.session.commit()
        print(f"Inserted {len(valid_airlines)} active airlines.")

        print("Loading Delay Records...")
        records_added = 0
        with open('Airline_Delay_Cause.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only add the record if BOTH the airline and airport are in our filtered DB
                airline_code = row['carrier']
                airport_code = row['airport']
                
                if airline_code in valid_airlines and airport_code in valid_airports:
                    record = DelayRecord(
                        airline_id=valid_airlines[airline_code].id,
                        airport_id=valid_airports[airport_code].id,
                        year=int(row['year']),
                        month=int(row['month']),
                        arr_flights=float(row['arr_flights'] or 0),
                        arr_del15=float(row['arr_del15'] or 0),
                        carrier_delay=float(row['carrier_delay'] or 0),
                        weather_delay=float(row['weather_delay'] or 0),
                        nas_delay=float(row['nas_delay'] or 0),
                        security_delay=float(row['security_delay'] or 0),
                        late_aircraft_delay=float(row['late_aircraft_delay'] or 0)
                    )
                    db.session.add(record)
                    records_added += 1
        db.session.commit()
        print(f"Inserted {records_added} relevant delay records.")
        print("Database successfully seeded!")

if __name__ == '__main__':
    seed()