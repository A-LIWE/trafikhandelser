from dataclasses import dataclass
from datetime import datetime

@dataclass
class TrafficIncident:
    id: str
    header: str
    description: str
    lat: float
    lon: float
    start_time: datetime
    county: str
    raw_text: str
    formatted_text: str | None = None