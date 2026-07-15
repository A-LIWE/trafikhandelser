import anthropic
from models import TrafficIncident
from store import save_formatted_text

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Du är en assistent som formulerar om trafikolycksrapporter till naturligt, 
lättläst svenska. Var kortfattad, max 2 meningar. Inga tekniska koder eller förkortningar."""

async def format_incident(incident: TrafficIncident) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": incident.raw_text}
        ]
    )

    formatted = message.content[0].text
    await save_formatted_text(incident.id, formatted)
    return formatted