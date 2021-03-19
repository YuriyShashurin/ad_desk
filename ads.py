from flask import Flask,request,render_template, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import redis, os, datetime
from werkzeug.utils import secure_filename
import pickle


UPLOAD_FOLDER = './static/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'jfif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


cache_var = 'result'
mongo_client = MongoClient(host='localhost', port=27017)
db = mongo_client.ads
collection = db.ads
r_server = redis.StrictRedis(host='localhost', port=6379)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if r_server.get(cache_var):
        data_dict = r_server.get(cache_var)
        data = pickle.loads(data_dict)
        print('Cache')
        return render_template('index.html', **data)
    else:
        data = collection.find()
        context = {
            'data_ads': [ad for ad in data],
        }
        print('Mongo')
        return render_template('index.html', **context)

@app.route('/create', methods=['GET', 'POST'])
def create_ads():
    if request.method == 'POST':

        photo = request.files['photo']

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(filename)

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

        collection.insert_one(new_data)

        result = collection.find()
        context = {'data_ads': [ad for ad in result],}
        data_dict = pickle.dumps(context)
        r_server.set('result', data_dict)

        return redirect(url_for('index'))
    return render_template('create_ads.html')

@app.route('/list/<ads_id>', methods=['GET'])
def show_ad(ads_id):
    data = collection.find_one({"_id": ObjectId(ads_id)})

    return render_template('detail_ad.html', data=data)

@app.route('/delete/<ads_id>', methods=['GET', 'POST'])
def delete_ad(ads_id):
    collection.delete_one({"_id": ObjectId(ads_id)})

    result = collection.find()
    context = {'data_ads': [ad for ad in result], }
    data_dict = pickle.dumps(context)
    r_server.set('result', data_dict)

    return redirect(url_for('index'))

@app.route('/list/add_comment/<ads_id>', methods=['POST'])
def add_comment(ads_id):

    comment = {
        'username': request.form['username'],
        'comment': request.form['comment'],
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    collection.update_one({"_id": ObjectId(ads_id)}, {'$push': {"comments": comment}})

    result = collection.find()
    context = {'data_ads': [ad for ad in result], }
    data_dict = pickle.dumps(context)
    r_server.set('result', data_dict)

    return redirect(url_for('show_ad', ads_id=ads_id))

@app.route('/list/add_tag/<ads_id>', methods=['POST'])
def add_tag(ads_id):

    tag = request.form['tag']


    collection.update_one({"_id": ObjectId(ads_id)}, {'$push': {"tag": tag}})

    result = collection.find()
    context = {'data_ads': [ad for ad in result], }
    data_dict = pickle.dumps(context)
    r_server.set('result', data_dict)

    return redirect(url_for('show_ad', ads_id=ads_id))


@app.route('/stats/', methods=['GET','POST'])
def stats():
    if r_server.get(cache_var):
        data_dict = r_server.get(cache_var)
        data = pickle.loads(data_dict)

        return render_template('stats.html', **data)
    else:
        data = collection.find()
        context = {
            'data_ads': [ad for ad in data],
        }
        print('Mongo')
        return render_template('stats.html', **context)

@app.route('/stats/<ads_id>', methods=['GET','POST'])
def ad_stat(ads_id):
    data = collection.find_one({"_id": ObjectId(ads_id)})
    return render_template('ad_stats.html', data=data)

if __name__ == '__main__':
    app.run(debug=True,port=5000)