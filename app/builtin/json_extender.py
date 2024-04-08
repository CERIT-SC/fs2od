import json
from datetime import date, datetime


class JSONEncoder(json.JSONEncoder):
    """
    Extension of basic JSONEncoder class implementing encoding Python's date and datetime type into JSON
    """
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()

        super().default(o)
