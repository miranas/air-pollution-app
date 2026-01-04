import codecs
import re
import logging


# Function to decode Unicode escape sequencec -> UTF-8  
def decode_unicode_escapes(text: str) -> str:
    """
    Decode Unicode escape sequences (\\uXXXX) to proper UTF-8
    
    Args:
        text(str): Input string potentialy Unicode escape sequences
    
    Returns:
        str: Decoded text with proper UTF-8 characters
    
    Example:
        input: "LJ Be\u017eigrad"
        output: "LJ Bežigrad"
    """

    #Check for empty input
    if not text:
        return text
    try:
        print(f"DEBUG: Input: {repr(text)}")  # Debug line
        
        # Method 1: Try direct codecs decode  literal \uXXXX
        if '\\u' in text: # Check for literal \u in the string
            try:
                decoded = codecs.decode(text, 'unicode_escape')
                print(f"DEBUG: Codecs decode result: {repr(decoded)}")
                return decoded
            
            except Exception as e:
                print(f"DEBUG: Codecs decode failed: {e}")
        
                # Method 2: Manual regex replacement for Unicode escapes
                def replace_unicode(match):
                    """Convert unicode escape to character"""
                    code_point = int(match.group(1), 16) # match extracts hex string and converts hex to int, group(1) means first capture group of signs after \u
                    return chr(code_point) # Convert int code_point to character
                
                
                decoded = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)
                print(f"DEBUG: Regex decode result: {repr(decoded)}")
                return decoded
            
        print(f"DEBUG: No escapes found: {repr(text)}")
        return text          
            
           
    except Exception as e:
        logging.warning(f"Failed to decode Unicode escapes in: {text} - Error: {e}")
        # Ensure a string is returned on all code paths
        return text
    