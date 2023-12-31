from flask import Flask
from threading import Thread
from json_operations import load_json, update_json

import os
app = Flask("")

@app.route("/", methods=['POST', 'GET'])
def home():
  return str(load_json())

def run():
  app.run(host="0.0.0.0", port=8080)

def keep_alive():
  t = Thread(target=run)
  t.start()
  

