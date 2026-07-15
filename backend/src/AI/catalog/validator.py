import json
import jsonschema
import os
import logging

logger = logging.getLogger(__name__)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")

def validate_design_json(design_data: dict) -> bool:
    try:
        if not os.path.exists(SCHEMA_PATH):
            logger.warning("schema.json not found, skipping strict validation.")
            return True
            
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)
        jsonschema.validate(instance=design_data, schema=schema)
        return True
    except Exception as e:
        logger.error(f"Design validation failed: {e}")
        return False
