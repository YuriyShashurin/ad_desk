from flask import Flask,request,render_template, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import redis, os, datetime
from werkzeug.utils import secure_filename
import pickle
import json



UPLOAD_FOLDER = './static/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'jfif'])

PORT = os.environ.get('PORT', 5001)

HOST_MONGO = os.environ.get('HOST_MONGO','localhost')
HOST_REDIS = os.environ.get('HOST_REDIS','localhost')
print(HOST_REDIS)
print(HOST_MONGO)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Settings MongoDB and cache

mongo_client = MongoClient(host=HOST_MONGO, port=27018)
db = mongo_client.ads
collection = db.ads
print(collection)
r_server = redis.StrictRedis(host=HOST_REDIS, port=6379)

# Check format of uploaded files

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Checking for the existence of a cache

def check_cache(cache_var, type):
    if r_server.get(cache_var):
        print("Use cache")
        data_dict = r_server.get(cache_var)
        if type == 'all':
            data = pickle.loads(data_dict)
        else:
            data = pickle.loads(data_dict)
        return data
    else:
        print("Use DB")
        if type == 'detail':
            data = collection.find_one({"_id": ObjectId(cache_var)})
            return data
        data = collection.find()
        return data


# Save all ids in cache after any changes (Create/delete/add tag and comment)

def save_cache_all():
    result = collection.find()
    context = {'data_ads': [ad for ad in result], }
    data_dict = pickle.dumps(context)
    r_server.set('result', data_dict)

def save_cache_instance(id):

    data = collection.find_one({"_id": ObjectId(id)})
    data_dict = pickle.dumps(data)
    r_server.set("{}".format(id), data_dict)


# Show all instance

@app.route('/', methods=['GET', 'POST'])
def index():
    data = check_cache('result', 'all')
    try:
        return render_template('index.html', **data)
    except:
        return render_template('index.html')


# Create new instance

@app.route('/create', methods=['GET', 'POST'])
def create_ads():
    if request.method == 'POST':

        photo = request.files['photo']

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_data = {
            'title': request.form['title'],
            'text': request.form['text'],
            'user': request.form['user'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'photo': filename,
            'city': request.form['city'],
            'cost': request.form['cost'],
            'status': 'active',
            'tags': [],
            'comments': [],
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        }

        a = collection.insert_one(new_data)
        id = a.inserted_id
        save_cache_all()
        save_cache_instance(id)
        return redirect(url_for('index'))

    return render_template('create_ads.html')


# Show detail by id

@app.route('/list/<ads_id>', methods=['GET'])
def show_ad(ads_id):
    data = check_cache(ads_id, 'detail')

    return render_template('detail_ad.html', data=data)


# Delete instance by id

@app.route('/delete/<ads_id>', methods=['GET', 'POST'])
def delete_ad(ads_id):
    collection.delete_one({"_id": ObjectId(ads_id)})

    save_cache_all()

    return redirect(url_for('index'))


# add comment in instance card

@app.route('/list/add_comment/<ads_id>', methods=['POST'])
def add_comment(ads_id):

    comment = {
        'username': request.form['username'],
        'comment': request.form['comment'],
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    collection.update_one({"_id": ObjectId(ads_id)}, {'$push': {"comments": comment}})

    save_cache_all()
    save_cache_instance(ads_id)

    return redirect(url_for('show_ad', ads_id=ads_id))


# add tag in instance card

@app.route('/list/add_tag/<ads_id>', methods=['POST'])
def add_tag(ads_id):

    tag = request.form['tag']

    collection.update_one({"_id": ObjectId(ads_id)}, {'$push': {"tags": tag}})

    save_cache_all()
    save_cache_instance(ads_id)

    return redirect(url_for('show_ad', ads_id=ads_id))


@app.route('/stats/', methods=['GET','POST'])
def stats():
    data = check_cache('result', 'all')
    print('Mongo')
    return render_template('stats.html', **data)

@app.route('/stats/<ads_id>', methods=['GET','POST'])
def ad_stat(ads_id):
    data = check_cache(ads_id, 'detail')
    return render_template('ad_stats.html', data=data)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=PORT)