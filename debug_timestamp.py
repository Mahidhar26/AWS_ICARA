#!/usr/bin/env python3
"""Debug timestamp parsing issue."""

from datetime import datetime

def test_timestamp_parsing():
    timestamp = '2024-10-15T22:30:00Z'
    print(f"Original timestamp: {timestamp}")
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        print(f"Parsed datetime: {dt}")
        print(f"Hour: {dt.hour}")
        
        if dt.hour < 7 or dt.hour > 19:
            print("Should be after hours: True")
        else:
            print("Should be after hours: False")
            
    except Exception as e:
        print(f"Error parsing: {e}")

if __name__ == "__main__":
    test_timestamp_parsing()