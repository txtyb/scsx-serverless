from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests, json

SCSX_TOKEN = os.environ['SCSX_TOKEN']
SCSX_HOST = os.environ['SCSX_HOST']

app = Flask(__name__)

cors = CORS(app)

@app.route('/api/getDevice', methods=['GET'])
def getDevice():
    def isDataValid(payloadData):
        if (len(payloadData) == 18) and (payloadData[0:2] == 'AA') and (payloadData[-2:] == '0F'):
            return True
        else:
            return False

    url = 'http://' + SCSX_HOST + '/api/v1/lorawan/datas/devices'

    n = request.args.get('n', type=int, default=10)
    devEui = request.args.get('devEui', type=str, default=None)
    typeArg = request.args.get('type', type=int, default=0)

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
    if resDate['code'] == 9001:
        return 'Invalid authentication token', 401
    elif resDate['msg'] == '请求成功':
        # reverse to make the last the latest
        content = resDate['data']['content'][::-1]
        dataUpList = list()
        dataType = ['光照', '温度', '湿度', '气压']
        for i in content:
            if i['mtypeText'] == 'CONFIRMED_DATA_UP':
                payloadData = i['payloadData']
                if isDataValid(payloadData):
                    dataUp = dict()
                    dataUp['type'] = dataType[int(payloadData[7])-1]
                    dataUp['timestamp'] = i['serverTimeMillis']
                    dataUp['time'] = i['serverTime']
                    dataUp['data'] = i['payloadData']
                    hexStr1 = '0x' + payloadData[10:14]
                    hexStr2 = '0x' + payloadData[14:16]
                    dataUp['value'] = float.fromhex(hexStr1) + (float.fromhex(hexStr2)*0.01)

                    dataUpList.append(dataUp)

        chartData = list()
        chartData.append(['Time', dataType[typeArg]])
        for i in dataUpList:
            if i['type'] == dataType[typeArg]:
                chartData.append([i['timestamp'], i['value']])

        return jsonify(chartData)

if __name__ == '__main__':
    app.run()
