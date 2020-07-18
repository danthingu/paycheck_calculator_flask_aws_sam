import json
import sys
from types import TracebackType
from typing import Type, Union

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from flask_lambda import FlaskLambda
from flask import request


app = FlaskLambda(__name__)
ddb = boto3.resource('dynamodb')
table = ddb.Table('members')


@app.route('/')
def index():
    return json_response({"message": "1234Hello, world!"})

def json_response(data, response_code=200):
    return json.dumps(data), response_code, {'Content-Type': 'application/json'}


if __name__ == "__main__":
    app.run(port=5000, debug=True)