from flask_pymongo import pymongo
from flask import Flask, jsonify, request, Response
from bson.json_util import dumps
import json
import numpy as np
import random

client = pymongo.MongoClient("mongodb://localhost:27017/")

#client = pymongo.MongoClient("mongodb://cervicuser:12345@10.128.0.8:27017/?authSource=cervic_database")
#client = pymongo.MongoClient("mongodb://cervicuser:12345@35.232.108.197:27017/?authSource=cervic_database")

# databases
DB_CCA = client.get_database('expert_prediction')
DB_VIA = client.get_database('expert_prediction_via')
DB_cervic = client.get_database('cervic_database')

# collections
db_via = pymongo.collection.Collection(DB_VIA, 'predictions_list')
db2_via = pymongo.collection.Collection(DB_VIA, 'predictions_status')
db3_via = pymongo.collection.Collection(DB_VIA, 'expert_stats')

db_cca = pymongo.collection.Collection(DB_CCA, 'predictions_list')
db2_cca = pymongo.collection.Collection(DB_CCA, 'predictions_status')
db3_cca = pymongo.collection.Collection(DB_CCA, 'expert_stats')

db4 = pymongo.collection.Collection(DB_VIA, 'expert_feed_data')


app = Flask(__name__)


@app.route('/expert_roi_submitted')
def expert_roi_submitted():
    expert = str(request.args.get('expert'))
    expert_for = int(request.args.get('expert_for'))
    
    if expert_for == 0:
        db = db_cca
    else:
        db = db_via

    q = db.find({"Expert": f"{expert}"})
    r = dumps(q)
    return r


@app.route('/new_submit', methods=['POST'])
def new_submit():
    roi_count = request.args.get("roi_count")
    expert = request.args.get("expert")
    test_id = request.args.get("Test_id")
    expert_for = int(request.args.get("expert_for"))
    
    # switch databases 
    #CCA
    if expert_for == 0:
        db = db_cca
        db2 = db2_cca
        db3 = db3_cca
    #VIA
    else:
        db = db_via
        db2 = db2_via
        db3 = db3_via

    # Enter the ROI data into DB
    db.insert_one(json.loads(request.data))

    # How many ROI already submitted?
    roi_submitted = db.find({"$and": [{"Expert": f"{expert}"}, {"Test_id": f"{test_id}"}]})
    roi_submitted_json = json.loads(dumps(roi_submitted))
    

    count = 0
    roi_submitted = []
    for i in roi_submitted_json:
        if i not in roi_submitted:
            count += 1
            roi_submitted.append(i['Roi_number'])

    # update db2
    db2_entry = json.loads(dumps(db2.find({"$and": [{"Expert": f"{expert}"}, {"Test_id": f"{test_id}"}]})))

    if not db2_entry:
        # make new entry
        if int(count) >= int(roi_count):
            j1 = '{"Expert": "' + str(expert) + '", "complete" : "yes' + '", "max_roi": "' + str(
            roi_count) + '", "Test_id": "' + str(test_id) + '", "roi_submitted_count": "' + str(
            count) + '", "roi_submitted": ""}'
        else:
            j1 = '{"Expert": "' + str(expert) + '", "complete" : "no' + '", "max_roi": "' + str(
            roi_count) + '", "Test_id": "' + str(test_id) + '", "roi_submitted_count": "' + str(
            count) + '", "roi_submitted": ""}'

        j2 = json.loads(j1)
        j2['roi_submitted'] = roi_submitted
        jf = json.loads(json.dumps(j2))
        db2.insert_one(jf)
    else:
        # replace
        if int(roi_count) == int(count):
            # complete = yes 
            j1 = '{"Expert": "' + str(expert) + '", "complete" : "yes' + '", "max_roi": "' + str(
                roi_count) + '", "Test_id": "' + str(test_id) + '", "roi_submitted_count": "' + str(
                count) + '", "roi_submitted": ""}'
        else:
            # complete = no
            j1 = '{"Expert": "' + str(expert) + '", "complete" : "no' + '", "max_roi": "' + str(
                roi_count) + '", "Test_id": "' + str(test_id) + '", "roi_submitted_count": "' + str(
                count) + '", "roi_submitted": ""}'
        j2 = json.loads(j1)
        j2['roi_submitted'] = roi_submitted
        jf = json.loads(json.dumps(j2))
        db2.replace_one({"$and": [{"Expert": f"{expert}"}, {"Test_id": f"{test_id}"}]}, jf)
    return {'inserted': 'true'}, 200


@app.route('/expert_stats', methods=['POST'])
def expert_stats():
    expert_for = int(request.args.get("expert_for"))
    
    if expert_for == 0:
        db3 = db3_cca
    else:
        db3 = db3_via

    inserted = db3.insert_one(json.loads(request.data))
    if(inserted.inserted_id!=''):
        return {'inserted': 'true'}, 200
    else:
        return {'inserted': 'false'}, 201


@app.route('/expert_stats_latest', methods=['GET'])
def expert_stats_latest():
    expert = str(request.args.get('expert'))
    expert_for = int(request.args.get("expert_for"))

    if expert_for == 0:
        db3 = db3_cca
    else:
        db3 = db3_via

    try:
        q = db3.find({"Expert": f"{expert}"}).sort("_id", -1)
        q_bson = dumps(q)
        q_json = json.loads(q_bson)
        return q_json[0]
    except:
        '''
        { "_id" : ObjectId("5f2a6ac60a7e0f17881138a1"), "Expert" : "expert3", "total_session_time" : "00:01:48", "session_date_time" : "8/5/2020, 1:46:06 PM", "num_roi_session" : "2", "num_test_session" : "0" }
        '''
        q_json = {"Expert":f"{expert}", "total_session_time": "none", "session_data_time": "none", "num_roi_session": "none", "num_test_session": "none"}
        return q_json


@app.route('/expert_stats_average', methods=['GET'])
def expert_stats_average():
    
    expert_for = int(request.args.get("expert_for"))
    
    if expert_for == 0:
        db3 = db3_cca
    else:
        db3 = db3_via
    
    num_roi_session_sum = 0
    total_session_time_sum = 0
    try:
        count = 0
        expert = str(request.args.get('expert'))
        q = db3.find({"Expert": f"{expert}"})
        q_bson = dumps(q)
        q_json = json.loads(q_bson)
        for i in q_json:
            count += 1
            num_roi_session_sum += int(i['num_roi_session'])
            t = i['total_session_time']
            ts = t.split(':')
            ms = int(ts[0])*60*60 + int(ts[1])*60 + int(ts[2])
            total_session_time_sum += ms

        num_roi_session_avg = round(num_roi_session_sum / count, 2)
        total_session_time_avg = total_session_time_sum / count
    except:
        json_ = dumps({"avg_session_time": "none", "avg_num_roi_session": "none"})
        return json_

    seconds = total_session_time_avg
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
      
    avg_session_time = "%02d:%02d:%02d" % (hour, minutes, seconds)

    json_ = dumps({"avg_session_time": f"{avg_session_time}", "avg_num_roi_session": f"{num_roi_session_avg}"})
    return json_


@app.route('/expert_test_submitted', methods=['GET'])
def expert_test_submitted():
    expert_for = int(request.args.get("expert_for"))
    expert = request.args.get('expert')
    
    if expert_for == 0:
        db2 = db2_cca
    else:
        db2 = db2_via
    
    q = dumps(db2.find({"Expert": f"{expert}"}))
    return q


@app.route('/expert_test_submitted_incomplete_roi', methods=['GET'])
def expert_test_submitted_incomplete_roi():
    expert_for = int(request.args.get("expert_for"))
    expert = request.args.get('expert')
    
    if expert_for == 0:
        db2 = db2_cca
    else:
        db2 = db2_via
    
    testId = request.args.get('Test_id')
    q = dumps(db2.find({"$and": [{"Expert": f"{expert}"}, {"Test_id": f"{testId}"}]}))
    return q


@app.route('/expert_feed_data_insert', methods=['POST'])
def expert_feed_data_insert():
    inserted = db4.insert_one(json.loads(request.data))
    if(inserted.inserted_id!=''):
        return {'inserted': 'true'}, 200
    else:
        return {'inserted': 'false'}, 201


@app.route("/expert_feed_progress_bar", methods=['GET'])
def expert_feed_progress_bar():
    hospital = str(request.args.get('hospital'))
    expert_for = int(request.args.get('expert_for'))
    expert  = request.args.get('expert')
    if expert_for == 0:
        db5 = pymongo.collection.Collection(DB_cervic, hospital)
        db5_test_data = json.loads(dumps(db5.find({'hosp_pres': hospital}, {'Test_id':1})))
        count = len(db5_test_data);
        done = json.loads(dumps(db2_cca.find({"Expert": f"{expert}"})))
        done_count = len(done);
        return {'total': count, 'done': done_count}
    if expert_for == 1:
        done = json.loads(dumps(db2_via.find({"Expert": f"{expert}"})))
        done_count = len(done);
        fc = int(dumps(db4.find().count()))
        return {'total': fc, 'done': done_count} 


@app.route('/expert_feed_data_random_roi', methods=['GET'])
def expert_feed_data_random_roi():
    expert = str(request.args.get('expert'))
    expert_for = int(request.args.get("expert_for"))
    
    if expert_for == 0:
        hospital = str(request.args.get('hosp_pres'))
        db2 = db2_cca
    else:
        db2 = db2_via
    
    lo = json.loads(dumps(db2.find()))

    left_over = []
    
    for i in lo:
        if i['complete'] == 'no' and i['Expert']==expert:
            left_over = i
   
    if left_over == []:
        
        if expert_for == 0:
            # access cervic_database
            db5 = pymongo.collection.Collection(DB_cervic, hospital)
            db5_test_data = json.loads(dumps(db5.find({'hosp_pres': hospital}, {'Test_id':1})))
            all_list = []
            for i in db5_test_data:
                all_list.append(i['Test_id'])
        else:
            fc = int(dumps(db4.find().count()))
            print("************************************************",fc)
            all_ = np.arange(0, fc, 1).tolist()
            
            all_list = []
            for i in all_:
                all_list.append('Test'+str(i))
        done = json.loads(dumps(db2.find({"Expert": f"{expert}"})))
        done_list = []
        for i in done:
            ti = i['Test_id']
            done_list.append(ti)
        done_list = list(set(done_list))
        not_done_list = []
        for i in all_list:
            if i not in done_list:
                not_done_list.append(i)
        if(not_done_list!=[]):
            random_test = random.choice(not_done_list)
            print("Current random test", random_test)
            r = {"random_test" : f"{random_test}", "left_over" : "no"}
        else:
            print("No random test")
            r = {"random_test" : "none", "left_over": "no"}
       
        print("####################################", r)
        return r
    else:
        test_id = left_over['Test_id']
        roi_submitted_count = left_over['roi_submitted_count']
        r = {"random_test" : f"{test_id}", "left_over": "yes", "roi_submitted_count": f"{roi_submitted_count}"}
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%", r)
        return r


@app.route('/expert_feed_data_roi_count', methods=['GET'])
def expert_feed_data_roi_count():
    testId = request.args.get('Test_id')
    rc = json.loads(dumps(db4.find({'test_id' : f'{testId}'})))
    for i in rc:
        roi_count = i['roi_count']
    r = {"roi_count": f"{roi_count}"}
    return r


@app.route('/expert_feed_data_roi_data', methods=['GET'])
def expert_feed_data_roi_data():
    testId = request.args.get('Test_id')
    roi_num = int(request.args.get('Roi_num'))
    rc = json.loads(dumps(db4.find({'test_id' : f'{testId}'})))
    for i in rc:
        main_image = i['roi_list'][roi_num]['main_image']

    r = {"main_image" : f"{main_image}"}
    return r


app.run(host='0.0.0.0', port=5002)
