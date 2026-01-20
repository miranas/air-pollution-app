from typing import Optional, List
from sqlalchemy import Integer, String, Float,DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from datetime import datetime


Base = declarative_base()


class DbModelStation(Base):
    __tablename__ = 'stations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[str] = mapped_column(String(50), nullable=False)
    station_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    d96_easting: Mapped[Optional[float]] = mapped_column(Float)
    d96_northing: Mapped[Optional[float]] = mapped_column(Float)
    elevation_meters: Mapped[Optional[float]] = mapped_column(Float)
    # Define the relationship to the  DbModelMeasurement class; It gives you a 
    # list of all DbModelMeasurements objects linked to this station
    station_measurements: Mapped[List["DbModelMeasurement"]] = relationship("DbModelMeasurement", back_populates="station")


class DbModelPollutant(Base):
    __tablename__ = 'pollutants'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(255), nullable=False)
    pollutant_measurements: Mapped[List["DbModelMeasurement"]] = relationship("DbModelMeasurement", back_populates="pollutant")


# Each measurement object represents one value for one pollutant, one station and one time
class DbModelMeasurement(Base):
    __tablename__ = 'measurements'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(Integer, ForeignKey('stations.id', ondelete="CASCADE"))
    pollutant_id: Mapped[int] = mapped_column(Integer, ForeignKey('pollutants.id', ondelete="CASCADE"))
    # float is a python object type in the model, Float is the SQLAlchemy database column type
    value: Mapped[float] = mapped_column(Float, nullable = True)
    # datetime is python object in my model, DateTime is the SQLAlchemy database column type
    measured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    station: Mapped[DbModelStation] = relationship("DbModelStation", back_populates = "station_measurements")
    pollutant: Mapped[DbModelPollutant] = relationship("DbModelPollutant", back_populates="pollutant_measurements")

















