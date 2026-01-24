import pytest
from services.arso_service import AirQualityService

@pytest.fixture
def service():
    print ("Setting up AirQualityService fixture")
    return AirQualityService()

def test_air_quality_service(service: AirQualityService):
    assert service is not None
    print ("AirQualityService instance created successfully")

"""def test_service_initialization(service:AirQualityService):
    Test that AirQualityService is initalized correctly
    assert hasattr(AirQualityService)"""
    
    






