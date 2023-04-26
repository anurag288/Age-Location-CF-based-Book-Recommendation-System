from flask import Flask,render_template,request,redirect
import pickle
import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy

# Additional imports
import pandas as pd
import pickle

# Load the grouped_ratings DataFrame from the pickle file
with open('grouped_ratings.pkl', 'rb') as f:
    grouped_ratings = pickle.load(f)

# Define a function to get recommendations for a given age and country
def get_recommendations(age, country, num_recommendations=5):
    filtered_ratings = grouped_ratings[(grouped_ratings['Age'] == age) & (grouped_ratings['Country'] == country)]
    sorted_ratings = filtered_ratings.sort_values(by='Average-Rating', ascending=False)
    top_recommendations = sorted_ratings.head(num_recommendations)
    return top_recommendations

popular_df = pickle.load(open('popular.pkl','rb'))
pt = pickle.load(open('pt.pkl','rb'))
#books = pickle.load(open('books.pkl','rb'))
books = pd.read_pickle('books.pkl')
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with app.app_context():
    db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

@app.route('/home')
def home():
    return render_template('home.html',book_name = list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_rating'].values))



@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Validate email and password fields
        if not email or not password:
            return render_template('login.html', error='Email and password are required')

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            return redirect('/home')
        else:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return render_template('login.html')
    
    return render_template('register.html')
    

@app.route('/login_validation', methods=['POST'])
def login_validation():
    email=request.form.get('email')
    password=request.form.get('password')
    return "The email is {} and the password is {}".format(email,password)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/age')
def age():
    return render_template('age.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/recommend_age_country', methods=['POST'])
def recommend_age_country():
    age = int(request.form['age'])
    country = request.form['country']
    recommendations = get_recommendations(age, country)
    return render_template('rem.html', recommendations=recommendations.to_dict(orient='records'))


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    index = np.where(pt.index == user_input)[0]
    if len(index) == 0:
        message = f"Sorry, data for '{user_input}' is not available."
        return render_template('recommend.html', message=message)
    index = index[0]

    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        if temp_df.empty:
            print(f"Data for {pt.index[i[0]]} is not available.")
            continue
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    search_book = books[books['Book-Title'].str.contains(user_input, case=False)].drop_duplicates('Book-Title').iloc[0]
    search_book_image_url = search_book['Image-URL-M']

    return render_template('recommend.html', data=data, search_query=user_input, search_book_image_url=search_book_image_url)



if __name__=="__main__":
    app.run(debug=True)

    