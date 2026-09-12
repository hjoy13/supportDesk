from django.conf import settings
from google import genai
from rest_framework.exceptions import APIException
from rest_framework import status


from apps.accounts.models import User

class SuggestionServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Suggestion service is unavailable, try again."
    default_code = "Suggestion_service_unavailable"


def build_prompt(ticket, messages):
    conversation_lines = []

    for message in messages:
        speaker = "Agent" if message.author.role == User.Role.AGENT else "Customer"
        conversation_lines.append(f"{speaker}: {message.text}")
    conversation_text = "\n".join(conversation_lines) if conversation_lines else "(no messages yet)"

    return (
        "You are a customer support agent replying to a support ticket.\n"
        "Write a short, professional, empathetic reply to the customer's most recent message.\n"
        "Only draft the reply text. Do not decide or mention ticket status, priority, or assignment.\n\n"
        f"Ticket title: {ticket.title}\n"
        f"Ticket description: {ticket.description}\n\n"
        "Conversation so far:\n"
        f"{conversation_text}\n\n"
        "Write the next reply, from the agent's perspective."
    )    

def get_suggested_reply(ticket, messages):
    prompt = build_prompt(ticket, messages)

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt,
        )

    except Exception:
        raise SuggestionServiceUnavailable()

    return interaction.output_text    
