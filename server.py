import glob
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import base64
from io import BytesIO
import datetime
import subprocess

from pymongo import MongoClient
import pymongo
from bson.json_util import dumps, loads


def get_data(data):
    data['_id'] = str(data['_id'])
    return data


app = Flask(__name__)
CORS(app)

IMAGE_PATH = "/image/*"
DETECT_PY_BASE_PATH = "/root/app/yolov5ForCouple/"

@app.route('/api/motion', methods=['POST'])
def save_picture():
    # count
    with open('count.json') as f:
        df = json.load(f)
        cnt = df['count']

    with open('count.json','w') as f:
        df['count'] += 1
        json.dump(df, f)

    with MongoClient("mongodb://localhost:27017") as client:
        yolo5coupledb = client.yolo5couple
        my_collection = yolo5coupledb.yolo5coupleSample

        yolov5obj = {
            "id" : 1,
            "data" : "hogehoge"
        }
        my_collection.insert_one(yolov5obj)

        assert client is not None

    print(cnt)
    print(request.files)
    # file name
    fs = request.files['imageFile']
    # # file save
    fs.save(os.getcwd() + '/image/' + fs.filename)

    if cnt % 5 == 0:
        print("call subprocess. /root/app/Yolo5Couple/detect.py start!")
        subprocess.check_call(['python',DETECT_PY_BASE_PATH + 'detect.py', '--source', os.getcwd() + '/image/' + fs.filename, '--weight','/root/app/yolov5ForCouple/best_20210926.pt'])
        print("call subprocess. /root/app/Yolo5Couple/detect.py end!")

    return "ok"


@app.route('/api/yolov5/pictures', methods=['GET'])
def get_yolov5_pictures():
    with MongoClient("mongodb://localhost:27017") as client:
        yolo5coupledb = client.yolov5couple
        my_collection = yolo5coupledb.yolov5couple2

        print(type(my_collection))

        objects = my_collection.find()
        temp = [get_data(i) for i in objects]

        for item in temp:
            print(item['msg'])
            try:
                with open(item['img'], "rb") as img_file:
                    item['base64'] = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception:
                print("[error] file not found...")

    return jsonify({"result" : temp})

@app.route('/api/picture', methods=['GET'])
def get_picture(pictureId):
    return ""

@app.route('/api/pictures', methods=['GET'])
def get_pictures():

    fileList = []
    files = glob.glob(os.getcwd() + IMAGE_PATH)

    print(os.getcwd() + IMAGE_PATH)
    idx = 1
    for f in files:
        #print(f)
        with open(f, "rb") as img_file:
            file_date = f.split('-')[1]
            file_time = file_date[8:10] + ':' + file_date[10:12]
            #print(file_time)
            img = {
                "id": idx,
                "file_name" : f,
                "file_date" : file_date[:8],
                "file_time" : file_time,
                "img" : base64.b64encode(img_file.read()).decode('utf-8')
            }
            idx = idx + 1
            fileList.append(img)

    return jsonify({"fileList" : fileList})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port=5000)
