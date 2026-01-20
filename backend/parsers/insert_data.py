from backend.database.session import SessionLocal
from backend.database.db_models import DbModelStation, DbModelPollutant, DbModelMeasurement
from backend.parsers.models.measurement_model import ParsedMeasurementModel
from backend.parsers.models.station_models import ParsedStationModel
from sqlalchemy.orm import Session


"""
This module takes parsed ParsedMeasurementModel and ParsedStationModel objects
and inserts them into database using 
SQLAlchemy models DbModelStation and DbModelMeasurement 

"""

def ensure_pollutants_in_db(db:Session):
    # Get existing pollutant names from DB
    existing_pollutant = {pollutant.name for pollutant in db.query(DbModelPollutant).all()}

    # Extract pollutant names from the dataclass
    all_fields = ParsedMeasurementModel.__dataclass_fields__.keys()
    non_pollutant_fields = {"station_id","station_name","time_from","time_to"}
    pollutant_fields = [field for field in all_fields if field not in non_pollutant_fields]

    # Insert missing pollutants into database
    for field in pollutant_fields:
        if field not in existing_pollutant:
            new_pollutant = DbModelPollutant(name = field, unit = "μg/m³" if field != "co" else "mg/m³")
            db.add(new_pollutant)
            db.commit()



# Function to insert stations and measurements into the database
def insert_data_into_db(db: Session, parsed_stations: ParsedStationModel, parsed_measurements: ParsedMeasurementModel):

    """
    Insert a station and all measurements for all pollutants into the database.
    Arguments:
    - parsed_stations: an object (parsing model StationInfo) with station attributes
    - parsed_measurements: an object (parsing model ParseMeasurements) with pollutant values as attributes
    """

    try:
        # Check if the station already exists, querying the database using SQLAlcchemy ORM. 
        db_single_station = db.query(DbModelStation).filter_by(station_id=parsed_stations.station_id).first()
        # if the station doesn't exist, create a new one:
        if not db_single_station:
            
            db_single_station = DbModelStation(
                # Map all attributes from ParsedStationModel to DbModelStation
                station_id = parsed_stations.station_id,
                station_name = parsed_stations.station_name,
                latitude = parsed_stations.latitude,
                longitude = parsed_stations.longitude,
                d96_easting = parsed_stations.d96_easting,
                d96_northing = parsed_stations.d96_northing,
                elevation_meters = parsed_stations.elevation_meters                
            )

            # Add the new station to the session
            db.add(db_single_station)
            db.commit()
          

        # parsed_measurements is a ParsedMeasurementModel instance
        # This loop creates one DbModelPollutant instance for each pollutant
        # with a value and time for the station
        db_pollutants = db.query(DbModelPollutant).all()
        measurement_time = getattr(parsed_measurements, "time_to", None)

        for single_pollutant in db_pollutants:
            name = single_pollutant.name # e.g. co, nox ..

            # gets the value from parsed_measurements, dinamically access the attribute
            # of parsed_measurements object using names from database pollutant model
            # getattr always gets the attribute value or None so in this case the value of 'name'
            value = getattr(parsed_measurements, name, None)
            
            if value is not None:
                single_pollutant_measurement = DbModelMeasurement(
                    station_id = db_single_station.id, # from db_single_station object
                    pollutant_id = single_pollutant.id,
                    value = value,
                    measured_at = measurement_time
                )

                db.add(single_pollutant_measurement)
                
        # should not commit/close here; caller manages the session lifecycle
     
    except Exception as e:
        db.rollback()
        print(f"Error inserting in database: {e}")
        


def insert_all_data(all_parsed_data: list[tuple[ParsedStationModel, ParsedMeasurementModel]]):
    """
    all_parsed_data: list of (ParsedStationModel, ParsedMeasurementModel) tuples
    """
    # open session
    db = SessionLocal()
    try:
        ensure_pollutants_in_db(db)
        for parsed_station, parsed_measurements in all_parsed_data:
            insert_data_into_db(db, parsed_station, parsed_measurements)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error inserting in database: {e}")
    finally:
        db.close()
                  
                
                        



                    
                       
                

              