import logging
import os
logging.basicConfig(level=logging.DEBUG)

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler


from dotenv import load_dotenv
load_dotenv()

app = App()

import requests

@app.middleware
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.event("app_mention")
def app_mention(payload, say):
    arguments = payload['text'].split(' ')[1:]
    command, sub_command, remaining = unpack_commands(arguments)

    try:
        payload = {'sub_command': sub_command, 'args': remaining}
        result = requests.post(f"{os.getenv('BISHOP_URL')}{command}", json=payload)
        if result.status_code != 202:
            say(result.json()['message'])

        return result.json()['message'], result.status_code
    except Exception as e:
        message =  f"Error posting message: {e}"
        say(message)
        return message, 400


@app.event("app_home_opened")
def handle_app_home_opened_events(say):
    say('Proxy is available')


from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health():
    return 'OK', 200


@flask_app.route("/send", methods=["POST"])
def send():
    params = request.get_json()

    try:
        result = handler.app.client.chat_postMessage(
            channel=params["channel_id"],
            text=params["message"]
        )
        if result.status_code != 200:
            message = "Error posting message"
            logging.error(message)
            return message, result.status_code

        logging.info(result)
        return 'OK', result.status_code
    except Exception as e:
        message = f"Error posting message: {e}"
        logging.error(message)
        return message, 400


def unpack_commands(arguments):
    command = arguments.pop(0)
    try:
        sub_command = arguments.pop(0)
    except IndexError:
        sub_command = ''

    return (command, sub_command, arguments)
