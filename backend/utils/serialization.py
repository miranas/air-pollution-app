from typing import Any, Mapping, Union
from flask.json.provider import DefaultJSONProvider
from datetime import datetime




# Custom JSON provider to ensure UTF-8 encoding   
class UTF8JsonProvider(DefaultJSONProvider):
    def dumps(self, obj: Any, **kwargs: Any) -> str:

        """Custom JSON encoder for UTF-8 support
        This method is called every time jsonify() is used
        Args:
            obj: Python object to convert to json
            **kwargs: JSON formatting options"""
        
        kwargs['ensure_ascii'] = False
        kwargs['indent'] =  2
        kwargs['sort_keys'] = False

        return super().dumps(obj, **kwargs)



# Serialization function
def to_serializable(obj: Any) -> Union[Mapping[str, Any], str]:
    # for pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # for pydantic v1, dataclass
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Fallback: return string representation for all other types so function
    # always returns a Mapping or a str as declared.
    return str(obj)

