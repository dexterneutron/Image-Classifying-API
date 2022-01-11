from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess
import json

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.ImageRecognition
users = db['Users']

def user_exists(posted_username):
    if users.find_one({"Username": posted_username,}):
        return True
    return False

def count_tokens(username):
    num_tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    
    return int(num_tokens)

def verify_password(username, password):
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf-8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def verify_credentials(username, password):
    if not user_exists(username):
        return generate_return_dictionary(301, "Invalid Username"), True
    
    correct_pw = verify_password(username, password)
    if not correct_pw:
        return generate_return_dictionary(302, "Invalid Password"), True

    return None, False

def generate_return_dictionary(status, msg):
    ret_json = {
        "status": status,
        "msg" : msg
    }

    return ret_json

class Register(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData['username']

        if user_exists(username):
            msg ={
                "msg": "Invalid username",
                "status": 301
            }
            return jsonify(msg)

        password = postedData['password']
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        users.insert_one({
            "Username" : username,
            "Password" : hashed_pw,
            "Sentence" : "",
            "Tokens" : 10
        })

        return jsonify(generate_return_dictionary(200,"User created"))
        
class Verify(Resource):

    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']
        url = data['url']

        retJson, error = verify_credentials(username, password)

        if error:
            return jsonify(retJson)
        
        tokens = count_tokens(username)
        if tokens <= 0:
            return jsonify(generate_return_dictionary(303, "Not enough tokens"))
        r = requests.get(url)
        retJson = {}
        with open('temp.jpg', 'wb') as f:
            f.write(r.content)
            proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            ret = proc.communicate()[0]
            proc.wait()
            with open("text.txt") as f:
                retJson = json.load(f)


        users.update_one({
            "Username": username
        },{
            "$set":{
                "Tokens": tokens-1
            }
        })

        return retJson

class Refill(Resource):
    def post(self):
        master_pw = "abc.123"
        data = request.get_json()
        username = data['username']
        password = data['password']
        refill_amount = data['refill_amount']
        if not user_exists(username) or master_pw != password:
            return jsonify(generate_return_dictionary(302,"Invalid Credentials"))
        users.update_one({
        "Username": username
        },
        {"$set":{
            "Tokens": refill_amount
            }}
        )
        return jsonify(generate_return_dictionary(200,"Refill successfull"))

api.add_resource(Register, "/register")
api.add_resource(Verify, "/verify")
api.add_resource(Refill, '/refill')

if __name__=="__main__":
    app.run(debug=True, host='0.0.0.0') 