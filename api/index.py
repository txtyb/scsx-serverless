from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests

SCSX_TOKEN = os.environ['SCSX_TOKEN']
SCSX_HOST = os.environ['SCSX_HOST']

app = Flask(__name__)

cors = CORS(app)

@app.route('/api/getDevice', methods=['GET'])
def getDevice():
    url = 'http://' + SCSX_HOST + '/api/v1/lorawan/datas/devices'

    n = request.args.get('n', type=int, default=10)
    devEui = request.args.get('devEui', type=str, default=None)

    params = {
        'page': 0, 
        'pageSize': n, 
        'devEui': devEui
    }

    headers = {
        'Authorization': SCSX_TOKEN
    }

    response = requests.get(url=url, headers=headers, params=params)

    resDate = response.json()

    if resDate['msg'] == '请求成功':
        return jsonify(resDate['data']['content'])

if __name__ == '__main__':
    app.run()
