from typing import Any, Dict, List
import yaml
import jsonschema
from cron_conf import SCHEMADIR

def validate_config_schema(data: Any, name: str) -> None:
    """Check data against given schema"""
    filename = "{}/{}.yaml".format(SCHEMADIR, name)
    with open(filename) as file:
        schema = yaml.load(file)
    jsonschema.validate(data, schema)


class SchemaValidator:
    """Configuration file schema validation helper"""

    def __init__(self, schemas: List) -> None:
        self.schemas = {}  # type: Dict[str, Any]
        for name in schemas:
            filename = "{}/{}.yaml".format(SCHEMADIR, name)
            with open(filename) as file:
                self.schemas[name] = yaml.load(file)

    def validate(self, data: Any, name: str):
        """Validate data against JSON schema"""
        if name in self.schemas:
            jsonschema.validate(data, self.schemas[name])
        else:
            raise Exception("Schema not defined: {}".format(name))