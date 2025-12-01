from flask import Flask, jsonify, Blueprint, Response, request, session
import serial
import time
def connectSerial():
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1) 
bp = Blueprint('serialComs', __name__, url_prefix='/serialComs')
@bp.route('/', methods = ["GET"])
def sse():
    def pingstream():
        counter = 0
        while True:
            if counter > 1000:counter = 0
            print("sending bytes")
            counter += 1
            time.sleep(1)
            yield f"data: {counter}\n\n"
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET",
    }
    return Response(pingstream(), headers=headers)

