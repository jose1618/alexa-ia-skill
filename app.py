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

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak("Hola, soy tu asistente IA. ¿En qué puedo ayudarte?")
                .ask("¿Qué deseas saber?")
                .response)

class PreguntaAlIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("PreguntaAlIntent")(handler_input)
    def handle(self, handler_input):
        frase = handler_input.request_envelope.request.intent.slots["frase"].value
        client = anthropic.Anthropic()
        mensaje = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": frase}]
        )
        respuesta = mensaje.content[0].text
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
                .speak("¡Hasta luego!")
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
