"""Test file for MockDataGenerator """
import pytest
import sys
import os


#Add backend directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.stations import get_all_stations
from services.mock_data_generator import MockDataGenerator

class TestMockDataGenerator:
    """Test class for MockDataGenerator"""
    def setup_method(self):
        """setup before each test"""
        self.generator = MockDataGenerator()

    def test_generator_creator(self):
        """Test that generator instance is created"""
        assert self.generator is not None
        assert hasattr(self.generator, 'pollutant_ranges')
        assert isinstance(self.generator.pollutant_ranges, dict)
        print("Generator created successfully!")

    def test_pollutant_ranges_loaded(self):
        """test that pollutant_ranges are loaded"""
        expected_pollutants = {'pm2.5', 'pm10', 'no2', 'o3', 'so2', 'co'}
        """set() converts (['pm2.5', 'pm10', 'no2', 'o3', 'so2', 'co']) to {'pm2.5', 'pm10', 'no2', 'o3', 'so2', 'co'}"""
        actual_pollutants = set(self.generator.pollutant_ranges.keys())
        assert expected_pollutants == actual_pollutants

    def test_generate_polutant_value(self):
        """testing if values are generated"""
        for pollutant in self.generator.pollutant_ranges:
            value = self.generator.generate_pollutant_value(pollutant)
            assert isinstance(value, float)
            print(f"generated: {pollutant}: {value}")
            #assert value == self.generator.pollutant_ranges[pollutant]
    

    def test_generate_single_pollutant(self):
        """test that sigle pollutant data are loaded correcly"""
        pollutants = self.generator.pollutant_ranges.keys()
        for pollutant in pollutants:
            pollutant_value = self.generator.generate_pollutant_value(pollutant)
            assert isinstance(pollutant_value, float)     


    def test_generate_all_stations_data(self):
        """test that complete station data is generated correctly"""
        stations = get_all_stations()
        for station in stations:
            result = self.generator.generate_all_stations_data(station["id"])
            print(result)

    



    
           

    


        
    
        
