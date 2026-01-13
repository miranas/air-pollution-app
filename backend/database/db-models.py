from typing import Optional, List
from sqlalchemy import Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from datetime import datetime


Base = declarative_base()


class Station(Base):
    __tablename__ = 'stations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[str] = mapped_column(String(50), nullable=False)
    station_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    d96_easting: Mapped[Optional[float]] = mapped_column(Float)
    d96_northing: Mapped[Optional[float]] = mapped_column(Float)
    elevation_meters: Mapped[Optional[float]] = mapped_column(Float)
    # Define the relationship to the Measurement class; "station" is the attribute in Measurement used for the link
    # between the two classes (ForeignKey).
    measurements: Mapped[List["Measurement"]] = relationship("Measurement", back_populates="station")


class Pollutant(Base):
    __tablename__ = 'pollutants'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(255), nullable=False)
    measurements: Mapped[List["Measurement"]] = relationship("Measurement", back_populates="pollutant")


class Measurement(Base):
    __tablename__ = 'measurements'
    measurement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(Integer, ForeignKey('stations.id', ondelete="CASCADE"))
    pollutant_id: Mapped[int] = mapped_column(Integer, ForeignKey('pollutants.id', ondelete="CASCADE"))
    # float is a python object type in the model, Float is the SQLAlchemy database column type
    value: Mapped[float] = mapped_column(Float, nullable = True)
    # datetime is python object in my model, DateTime is the SQLAlchemy database column type
    measured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    station: Mapped[Station] = relationship("Station", back_populates = "measurements")
    pollutant: Mapped[Pollutant] = relationship("Pollutant", back_populates="measurements")

















