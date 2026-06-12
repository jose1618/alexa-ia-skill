import json
import logging
from flask import Flask, request, jsonify
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
import anthropic

app = Flask(__name__)
logger = logging.getLogger(__name__)
sb = SkillBuilder()

# Nombre y personalidad del asistente
NOMBRE_ASISTENTE = "Aria"
PERSONALIDAD = """Eres Aria, un asistente de inteligencia artificial amigable, 
inteligente y con sentido del humor. Respondes siempre en español de México, 
de forma clara y concisa. Tus respuestas son máximo de 3 oraciones para que 
Alexa pueda leerlas cómodamente. Eres curioso, empático y siempre dispuesto 
a ayudar. Cuando no sabes algo, lo admites con honestidad."""

# Memoria de conversación por sesión
conversaciones = {}

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    def handle(self, handler_input):
        session_id = handler_input.request_envelope.session.session_id
        conversaciones[session_id] = []
        return (handler_input.response_builder
                .speak(f"Hola, soy {NOMBRE_ASISTENTE}, tu asistente inteligente. ¿En qué puedo ayudarte hoy?")
                .ask("¿Qué deseas saber?")
                .response)

class PreguntaAlIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("PreguntaAlIntent")(handler_input)
    def handle(self, handler_input):
        session_id = handler_input.request_envelope.session.session_id
        frase = handler_input.request_envelope.request.intent.slots["frase"].value

        # Inicializar historial si no existe
        if session_id not in conversaciones:
            conversaciones[session_id] = []

        # Agregar pregunta al historial
        conversaciones[session_id].append({
            "role": "user",
            "content": frase
        })

        # Mantener solo las últimas 6 interacciones para no exceder límites
        historial = conversaciones[session_id][-20:]

        # Llamada a Claude con contexto y personalidad
        client = anthropic.Anthropic()
        mensaje = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=PERSONALIDAD,
            messages=historial
        )
        respuesta = mensaje.content[0].text

        # Guardar respuesta en historial
        conversaciones[session_id].append({
            "role": "assistant",
            "content": respuesta
        })

        return (handler_input.response_builder
                .speak(respuesta)
                .ask("¿Tienes otra pregunta?")
                .response)

class CancelStopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))
    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak(f"¡Hasta luego! Fue un placer ayudarte.")
                .response)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PreguntaAlIntentHandler())
sb.add_request_handler(CancelStopHandler())

skill = sb.create()

@app.route("/", methods=["POST"])
def index():
    body = request.json
    response = skill.invoke(
        request_envelope=skill.serializer.deserialize(
            json.dumps(body), __import__('ask_sdk_model').RequestEnvelope
        ),
        context=None
    )
    return jsonify(skill.serializer.serialize(response.response))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
