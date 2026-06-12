from flask import Flask
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_flask_adapter import Skill
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
import ask_sdk_core.utils.request_type_utils as is_request
import anthropic

app = Flask(__name__)
sb = SkillBuilder()

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request.is_launch_request(handler_input)
    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak("Hola, soy tu asistente IA. ¿En qué puedo ayudarte?")
                .ask("¿Qué deseas saber?")
                .response)

class PreguntaAlIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request.is_intent_request(handler_input, "PreguntaAlIntent")
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
        return (is_request.is_intent_request(handler_input, "AMAZON.CancelIntent") or
                is_request.is_intent_request(handler_input, "AMAZON.StopIntent"))
    def handle(self, handler_input):
        return (handler_input.response_builder
                .speak("¡Hasta luego!")
                .response)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PreguntaAlIntentHandler())
sb.add_request_handler(CancelStopHandler())

skill_adapter = Skill(skill=sb.create(), verify_signature=True, verify_timestamp=True)
app.add_url_rule("/", "index", skill_adapter.dispatch_request, methods=["POST"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
