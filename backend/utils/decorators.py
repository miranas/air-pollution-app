from functools import wraps
import time
import logging
from flask import jsonify


def add_timing(func):
    """Decorator to add response time to the JSON response"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs) #this calls the decorated function
        end_time = time.time()
        print(f"{func.__name__} took {end_time -start_time} sec")
        return result
    return wrapper


def handle_exceptions(func):
    """Decorator to handle exceptions and log them"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            logging.error(f"File not found  in {func.__name__}") 
            return jsonify({"Error":"DAta file not found"}),500
        except ValueError as e:
            logging.error(f"Value error in {func.__name__}:{str(e)}")
            return jsonify({"Error":"Invalid data format"}),400
        
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return jsonify({"Error":"Internal server error"}),500
    return wrapper
    

def handle_service_exception(func):
    """Decorator to handle exceptions in services"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            logging.error(f"File not found in {func.__name__}")
            return None
        except ValueError as e:
            logging.error(f"Value error in {func.__name__}:{str(e)}")
            return None
        except Exception as e:
            logging.error("Unexpected error in {func}:{str(e)}")
            return None
    return wrapper



    


