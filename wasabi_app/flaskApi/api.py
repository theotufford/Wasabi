from flask import Flask, jsonify, Blueprint, request
from flask_cors import CORS

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/', methods=["GET", "POST"])
def apiHandler(): # handle input from json calls and run the function from the global scope that they reference
    function_target = request.get_json()['function_target'] # get target function name
    function_args = request.get_json().get('args') # get target function args

    if not (function_target):
        return (jsonify({
            "error":{
                "message":"no function_target provided",
                "code":-1
                }
            }))
        pass

    targetFunction = globals().get(function_target)
    if not targetFunction:
        return (jsonify({
            "error":{
                "message":
                f"couldnt find function {function_target}", 
                "code":-2
                }
            }))
    functionReturn = targetFunction(function_args) # run target function with args via return 
    print(f"called {function_target} with {function_args}, function returned: {functionReturn}")
    return jsonify(functionReturn)



#note to anyone writing additional functions here, they should return a python dict NOT json, 
#the handler converts from dict to json

def baseFunction(args):
    return {"value":"this is my return value!", "argMirror":f"these were your arguments: {args}"}
