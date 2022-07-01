from email.policy import default
from tempfile import tempdir
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
        if (len(payloadData) == 18) and (payloadData[0:2] == 'AA') and (payloadData[-2:] == '0F') and (payloadData[6] == '0'):
            return True
        else:
            return False

    url = 'http://' + SCSX_HOST + '/api/v1/lorawan/datas/devices'

    n = request.args.get('n', type=int, default=10)
    devEuiList = request.args.getlist('devEui', type=str)
    # remove duplicate
    devEuiList = list(set(devEuiList))
    typeArg = request.args.get('type', type=int, default=0)

    headers = {
        'Authorization': SCSX_TOKEN
    }

    resDataList = list()

    for devEui in devEuiList:
        params = {
            'page': 0, 
            'pageSize': n, 
            'devEui': devEui
        }
        
        response = requests.get(url=url, headers=headers, params=params)

        resData = response.json()
        if resData['code'] == 9001:
            return 'Invalid authentication token', 401
        elif resData['msg'] == '请求成功':
            resDataList.append(resData)

    dataUpListBundle = list()
    for resData in resDataList:
        # reverse to make the last the latest
        content = resData['data']['content'][::-1]
        dataUpList = list()
        dataType = ['光照', '气压', '温度', '湿度']
        for i in content:
            if i['mtypeText'] == 'CONFIRMED_DATA_UP':
                payloadData = i['payloadData']
                if isDataValid(payloadData):
                    # print(payloadData[7])
                    if not ((int(payloadData[7])-1) == typeArg):
                        continue
                    dataUp = dict()
                    dataUp['type'] = dataType[int(payloadData[7])-1]
                    dataUp['timestamp'] = i['serverTimeMillis']
                    dataUp['time'] = i['serverTime']
                    dataUp['data'] = i['payloadData']
                    hexStr1 = '0x' + payloadData[10:14]
                    hexStr2 = '0x' + payloadData[14:16]
                    dataUp['value'] = float.fromhex(hexStr1) + (float.fromhex(hexStr2)*0.01)

                    dataUpList.append(dataUp)
        dataUpListBundle.append(dataUpList)

    chartData = list()
    firstlineTmp = ['Time'] 
    for devEui in devEuiList:
        firstlineTmp.append(devEui)
    chartData.append(firstlineTmp)
    
    for index, dataUpList in enumerate(dataUpListBundle):
        for i in dataUpList:
            tmpRow = list()
            timeFlag = False
            tmpIndex = int()
            for index2, row in enumerate(chartData[1:]):
                if row[0] == i['timestamp']:
                    timeFlag = True
                    tmpIndex = index2+1
                    break
            if not timeFlag:
                tmpRow = list(None for i in range(len(dataUpListBundle)+1))
                tmpRow[0] = i['timestamp']
                for j in range(len(dataUpListBundle)):
                    if j == index:
                        tmpRow[j+1] = i['value']
                    else:
                        tmpRow[j+1] = None
                chartData.append(tmpRow)
            else:
                chartData[tmpIndex][index+1] = i['value']

    return jsonify(chartData)

if __name__ == '__main__':
    app.run()
