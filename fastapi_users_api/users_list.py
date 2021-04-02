from flask_pymongo import pymongo
from flask import Flask, jsonify, request, Response
from bson.json_util import dumps
from typing import Optional
import json

client = pymongo.MongoClient("mongodb://localhost:27017/")

app = Flask(__name__)

# databases
DB_USERS = client.get_database('fastapi_users')
db_users = pymongo.collection.Collection(DB_USERS, 'users')

@app.route("/get_users_list", methods=['GET'])
def get_users_list():
    hosp_pres_ = request.args.get('hosp_pres')
    selectValue =  request.args.get('selectValue')
    searchText = request.args.get('searchText')
    item_size = request.args.get('item_size')
    last_id = request.args.get('last_id')

    if item_size == None:
       item_size = '10'

    print('item_size: ', item_size)

    if hosp_pres_ != None and selectValue != None and selectValue != None:
        userSearch = {"agency": f"{hosp_pres_}", f"{selectValue}": f"{searchText}" }
        userSearchRes = json.loads(dumps(db_users.find(userSearch, {'username':1, 'name':1, 'id':1, 'agency':1, 'role':1} ) ) )
        #userSearchResCount = json.loads(dumps(db_users.find(userSearch, {'username':1, 'name':1, 'id':1, 'agency':1, 'role':1}).count()  ) )
        return {'res': userSearchRes }
        #return {'res': userSearchRes, 'count': userSearchResCount}

    #initail call for pagination
    elif hosp_pres_ != None and last_id == 'first':
        userSearch = { "agency": f"{hosp_pres_}" }
        users = json.loads(dumps(db_users.find( userSearch, {'username':1, 'name':1, 'id':1, 'agency':1, 'role':1} ).sort([('_id', -1)]).limit(int(item_size)) ) )
        last_item_of_the_list = [x for x in users]
        if len(last_item_of_the_list) > 0:
                last_id_of_the_list = last_item_of_the_list[-1]['_id']
        return { 'users': users, "last_id": last_id_of_the_list }

    #next call
    elif hosp_pres_ != None and last_id != None and last_id != 'first':
        nextRes = { "agency": f"{hosp_pres_}" }

        #users = json.loads(dumps(db_users.find( nextRes, {'username':1, 'name':1, 'id':1, 'agency':1, 'role':1} ).sort([('_id', -1)]).limit(int(item_size)) ) )

        users = db_users.find({'_id': {'$lt': last_id}, 'agency': f"{hosp_pres_}" }).sort([('_id', -1)]).limit(int(item_size))

        #users = json.loads(dumps(db_users.find( {'_id': {'$lt': last_id}, "agency": f"{hosp_pres_}", 'username':1, 'name':1, 'id':1, 'agency':1, 'role':1 })))
        print({"hosp_pres": hosp_pres_})

        #last_item_of_the_list = [x for x in users]
        #if len(last_item_of_the_list) > 0:
        #        last_id_of_the_list = last_item_of_the_list[-1]['_id']
        #return { 'users': users, "last_id": last_id_of_the_list }
        return { 'users': users }

    elif last_id != None:
        users = json.loads(dumps(db_users.find().sort([('_id', -1)]).limit(int(item_size)) ) )
        last_item_of_the_list = [x for x in users]
        if len(last_item_of_the_list) > 0:
                last_id_of_the_list = last_item_of_the_list[-1]['_id']
        return { 'users': users, "last_id": last_id_of_the_list }

    else:
        #users = json.loads(dumps(db_users.find().sort([('_id', -1)]).limit(int(item_size)) ) )
        #last_item_of_the_list = [x for x in users]
        #if len(last_item_of_the_list) > 0:
        #        last_id_of_the_list = last_item_of_the_list[-1]['_id']
        #return { 'users': users, "last_id": last_id_of_the_list }

        userSearch = { "agency": f"{hosp_pres_}" }
        userSearchRes = json.loads(dumps(db_users.find( userSearch, {'username':1, 'name':1, 'id':1, 'agency':1, 'role':1} ) ) )
        #userSearchRes = json.loads(dumps(db_users.find( userSearch, { 'username':1 } ) ) )
        return {'users': userSearchRes }

app.run(host="0.0.0.0", port=8001)
