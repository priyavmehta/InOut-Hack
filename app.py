from flask import Flask,request, jsonify
import pymongo
import urllib
from flask_restful import Resource, Api
from model.social_distance_detector import detectSocialDistancing
import numpy as np
import cv2
from datetime import datetime
  
# Replace your URL here. Don't forget to replace the password. 
connection_url = 'mongodb+srv://priyavmehta:priyavmehta@inout.a9ism.mongodb.net/inout?retryWrites=true&w=majority'

app = Flask(__name__) 
client = pymongo.MongoClient(connection_url)
app.config['SECRET_KEY'] = 'assembler'

# Database
Database = client.get_database('inout')
# Table
LocationTable = Database.Locations

class Add(Resource):
    
    def get(self, name, id):
        queryObject = { 
            'Name': name, 
            'ID': id
        } 
        query = LocationTable.insert_one(queryObject) 
        return "Query inserted...!!!"

class Validate(Resource):

    def post(self):
        data = request.get_json()
        url = data['url']
        url_response = urllib.request.urlopen(url)
        img_array = np.array(bytearray(url_response.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)
        v = detectSocialDistancing(img)
        print(v)
        if (v[0] / v[1]) * 100 > 30:

            queryObject = {
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'datetime': datetime.now(),
                'imageURL': data['url']
            }

            query = LocationTable.insert_one(queryObject)
            print(query)
        return {"msg": "Total people violating the rules are : {}".format(v[0])}
        
class MapDetails(Resource):

    def get(self):

        data = LocationTable.find({})
        
        output = {} 
        dates = set()
        i = 0
        for x in data: 
            output[i] = x 
            date = output[i]['datetime']
            day, month, year = date.day, date.month, date.year
            date = datetime(year, month, day)
            dates.add(date)
            output[i].pop('_id')
            i += 1
        print(dates)
        data = dict()
        for date in dates:
            data[date] = []
        for key in output:
            thisDate = output[key]['datetime']
            thisDay, thisMonth, thisYear = thisDate.day, thisDate.month, thisDate.year
            thisDate = datetime(thisYear, thisMonth, thisDay)

            for date in dates:
                if date == thisDate:
                    data[date].append(key)
                    break

        print(data)
        return jsonify(output) 


api = Api(app)
api.add_resource(Add, '/insert-one/<string:name>/<int:id>')
api.add_resource(Validate, '/validate')
api.add_resource(MapDetails, '/details')

if __name__ == '__main__': 
    app.run(debug=True) 