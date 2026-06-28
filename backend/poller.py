import httpx
import xmltodict
from datetime import datetime
from models import TrafficIncident
from store import get_change_id, save_change_id, save_incident
import os

API_URL = "https://api.trafikinfo.trafikverket.se/v2/data.xml"

def build_query(change_id: str) -> str:
    api_key = os.getenv("TRAFIKVERKET_API_KEY")
    return f"""
    <REQUEST>
        <LOGIN authenticationkey="{api_key}"/>
        <QUERY objecttype="Situation" schemaversion="1.5" changeid="{change_id}">
            <FILTER>
                <EQ name="Deviation.MessageType" value="Olycka"/>
            </FILTER>
            <INCLUDE>Deviation.Id</INCLUDE>
            <INCLUDE>Deviation.Header</INCLUDE>
            <INCLUDE>Deviation.Description</INCLUDE>
            <INCLUDE>Deviation.Geometry.WGS84</INCLUDE>
            <INCLUDE>Deviation.StartTime</INCLUDE>
            <INCLUDE>Deviation.CountyNo</INCLUDE>
        </QUERY>
    </REQUEST>
    """

def parse_geometry(wgs84: str) -> tuple[float, float]:
    # Format: "POINT (lon lat)"
    coords = wgs84.replace("POINT (", "").replace(")", "").split()
    return float(coords[1]), float(coords[0])  # lat, lon

def parse_incidents(data: dict) -> tuple[list[TrafficIncident], str]:
    incidents = []
    response = data.get("RESPONSE", {})
    result = response.get("RESULT", {})
    change_id = result.get("@changeid", "0")
    
    situations = result.get("Situation", [])
    if isinstance(situations, dict):
        situations = [situations]

    for situation in situations:
        deviations = situation.get("Deviation", [])
        if isinstance(deviations, dict):
            deviations = [deviations]

        for dev in deviations:
            try:
                geometry = dev.get("Geometry", {}).get("WGS84", "")
                if not geometry:
                    continue

                lat, lon = parse_geometry(geometry)
                incident = TrafficIncident(
                    id=dev.get("Id", ""),
                    header=dev.get("Header", ""),
                    description=dev.get("Description", ""),
                    lat=lat,
                    lon=lon,
                    start_time=datetime.fromisoformat(dev.get("StartTime", "")),
                    county=str(dev.get("CountyNo", "")),
                    raw_text=dev.get("Description", "")
                )
                incidents.append(incident)
            except Exception as e:
                print(f"Failed to parse incident: {e}")
                continue

    return incidents, change_id

async def poll_trafikverket() -> list[TrafficIncident]:
    change_id = await get_change_id()
    query = build_query(change_id)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            content=query,
            headers={"Content-Type": "text/xml"}
        )
        response.raise_for_status()

    data = xmltodict.parse(response.text)
    incidents, new_change_id = parse_incidents(data)

    await save_change_id(new_change_id)
    for incident in incidents:
        await save_incident(incident)

    print(f"Found {len(incidents)} new incidents, changeid: {new_change_id}")
    return incidents