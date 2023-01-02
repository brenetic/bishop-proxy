import logging
import os
logging.basicConfig(level=logging.DEBUG)

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler


from dotenv import load_dotenv
load_dotenv()

from greeter import greeter

app = App()

import requests
import pdb

@app.middleware
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.event("app_mention")
def event_test(payload, say):
    arguments = payload['text'].split(' ')
    command, sub_command, remaining = arguments[1], arguments[2], arguments[3:]
    try:
        payload = {'sub_command': sub_command, 'args': remaining}
        result = requests.post(f"{os.getenv('BISHOP_URL')}{command}", json=payload)
        if result.status_code != 200:
            say(result.reason)
    except Exception as e:
        say(f"Error posting message: {e}")


@app.event("app_home_opened")
def handle_app_home_opened_events(say):
    say(greeter.greet())


from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/send", methods=["POST"])
def send():
    params = request.get_json()

    try:
        result = handler.app.client.chat_postMessage(
            channel=params["channel_id"],
            text=params["message"]
        )
        if result.status_code != 200:
            pdb.set_trace()
        logging.info(result)
    except Exception as e:
        logging.error(f"Error posting message: {e}")