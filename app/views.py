from app import app, db, lm
from flask import render_template, flash, redirect, url_for, request
from flask.ext.login import login_user, logout_user, current_user, login_required

from models import User, Post, Item, Meal, ROLE_ADMIN, ROLE_USER
from forms import LoginForm, CreateUserForm, AddPostForm, EditPostForm, DataUploadForm, AddFoodItemForm, AddMealForm, NlpForm
from nlpsandbox import Text, Sentence

from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename # For file uploading
import hashlib, datetime, os, csv, string

#------------------ User Management Views ----------------------

# Used by flask-login to load user
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    user = current_user
    title = 'Login'
    header = 'Login'
    if user is not None and user.is_authenticated():
        return redirect(request.args.get("next") or url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        hashed_password = hashlib.sha512(form.password.data).hexdigest()
        if user is not None and hashed_password == user.password:
            login_user(user)
            return redirect(request.args.get("next") or url_for("index"))
        elif user is None:
            user = current_user
            flash("There is no user with the email address " + form.email.data)
            return render_template('/login.html',
                            user = user,
                            title = title,
                            header = header,
                            form = form)
        else:
            user = current_user
            flash("Your password is incorrect")
            return render_template('/login.html',
                            user = user,
                            title = title,
                            header = header,
                            form = form)

    return render_template('/login.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#------------------ Public Views ----------------------

@app.route('/')
@app.route('/index')
def index():
    user = current_user
    title = 'Home'
    header = 'Welcome!'
    return render_template('index.html',
                           user = user,
                           title = title,
                           header = header)

@app.route('/tools')
def tools():
    user = current_user
    title = 'Tools'
    header = 'Tools'
    return render_template('tools.html',
                           user = user,
                           title = title,
                           header = header)


@app.route('/blog')
def blog():
    user = current_user
    title = 'Blog'
    header = 'Blog'

    posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template('blog.html',
                           user = user,
                           title = title,
                           header = header,
                           posts = posts)

#------------------ Admin Views ----------------------

@app.route('/create_user', methods = ['GET', 'POST'])
@login_required
def create_user():
    user = current_user
    title = 'Create User'
    header = 'Create a User'

    form = CreateUserForm()
    if form.validate_on_submit():
        hashed_password = hashlib.sha512(form.password.data).hexdigest()
        new_user = User(nickname=form.nickname.data, email=form.email.data, password=hashed_password)
        if form.is_admin.data:
            new_user.role = ROLE_ADMIN

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User "' + form.nickname.data + '" created!')
            return redirect('/index')
        except IntegrityError as e:
            flash(e.message)
            return redirect('/create_user')

    return render_template('create_user.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form)

@app.route('/add_blog_post', methods = ['GET', 'POST'])
@login_required
def add_blog_post():
    user = current_user

    title = 'Add Blog Post'
    header = 'Add a Blog Post'

    form = AddPostForm()
    if form.validate_on_submit():
        new_post = Post(user_id = user.id, title=form.title.data, content=form.content.data, timestamp=datetime.datetime.now())

        try:
            db.session.add(new_post)
            db.session.commit()
            flash('Post "' + form.title.data + '" added!')
            return redirect('/index')
        except IntegrityError as e:
            flash(e.message)
            return redirect('/add_blog_post')

    return render_template('add_blog_post.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form)

@app.route('/edit_blog_post/<post_id>', methods = ['GET', 'POST'])
@login_required
def edit_blog_post(post_id):
    user = current_user
    post = Post.query.filter_by(id = post_id).first_or_404()

    # Check that the user logged in is the post's author, if not redirect to index
    if (post.author.id != user.id):
        flash ("Only the author of this post can edit it.")
        return redirect('/index')

    title = 'Edit Blog Post'
    header = 'Edit a Blog Post'

    form = EditPostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        if form.update_ts.data:
            post.timestamp = datetime.datetime.now()

        try:
            db.session.commit()
            flash('Post "' + form.title.data + '" updated!')
            return redirect('/index')
        except e:
            flash(e.message)
            return redirect('/edit_blog_post/' + str(post_id))

    form.populate_obj(post)

    return render_template('edit_blog_post.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form,
                           post = post)

@app.route('/delete_blog_post/<post_id>', methods = ['GET','POST'])
@login_required
def delete_blog_post(post_id):
    user = current_user
    post = Post.query.filter_by(id = post_id).first_or_404()

    # Check that the user logged in is the post's author, if not redirect to index
    if (post.author.id != user.id):
        flash ("Only the author of this post can delete it.")
        return redirect('/index')

    post_title = post.title

    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post "' + post_title + '" deleted!')
        return redirect('/index')
    except e:
        flash(e.message)
        return redirect('/blog')


#------------------ SuperModeler Views ----------------------

# Helper view to determine if upload is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# Handle uploading file and setting y variable
@app.route('/data_upload', methods = ['GET','POST'])
@login_required
def data_upload():
    user = current_user
    title = 'Data Upload'
    header = 'Upload your Data'
    form = DataUploadForm()

    if form.validate_on_submit():
        if form.datafile.data:
            file = request.files['datafile']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                fullpath = app.config['UPLOAD_FOLDER'] + '/' + filename

                delimiter = form.delimiter_translator[form.delimiter.data]

                with open(fullpath, 'rb') as csvfile:
                    reader = csv.reader(csvfile, delimiter=delimiter, quotechar='"')
                    header_row = reader.next()

                form.y.choices = [(string.lower(g), g) for g in header_row]
                del form.delimiter

                return render_template('data_upload.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form,
                           datafile_name = filename)

        elif form.y.data != 'nodata':
            flash ('Data Upload Success!')
            redirect(url_for('index'))

    return render_template('data_upload.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form,
                           datafile_name = None)

# Food Planning App
@app.route('/food_planner', methods = ['GET','POST'])
@login_required
def food_planner():
    user = current_user
    title = 'Food Planner Dashboard'
    header = 'Food Planner Dashboard'
    meals = [meal for meal in user.meals]

    return render_template('food_dashboard.html',
                           user = user,
                           title = title,
                           header = header,
                           meals = meals)

@app.route('/return_meal_content', methods = ['GET','POST'])
@login_required
def return_meal_content():
    meal_id = int(request.form['meal_id'])
    meal = Meal.query.get(meal_id)

    return render_template('meal_content.html',
                           meal=meal)

@app.route('/add_food_item', methods = ['GET','POST'])
@login_required
def add_food_item():
    user = current_user
    title = 'Add Food Item'
    header = 'Add Food Item'
    form = AddFoodItemForm()

    if form.validate_on_submit():
        new_item = Item(label = form.label.data, cost=form.cost.data, volume=form.volume.data, increment=form.increment.data)

        try:
            db.session.add(new_item)
            db.session.commit()
            flash('Item "' + form.label.data + '" added!')
            return redirect('/food_planner_dashboard')
        except IntegrityError as e:
            flash(e.message)
            return redirect('/food_planner_dashboard')

    return render_template('add_food_item.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form)

@app.route('/add_meal', methods = ['GET','POST'])
@login_required
def add_meal():
    user = current_user
    title = 'Add Meal'
    header = 'Add Meal'
    form = AddMealForm()

    if form.validate_on_submit():
        new_meal = Meal(user_id = user.id, label = form.label.data, minutes=form.minutes.data, recipe=form.recipe.data)

        try:
            db.session.add(new_meal)
            db.session.commit()
            flash('Meal "' + form.label.data + '" added!')
            return redirect('/food_planner')
        except IntegrityError as e:
            flash(e.message)
            return redirect('/food_planner')

    return render_template('add_meal.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form)

# ------------------- nlp --------------------
import nltk

@app.route('/nlp', methods = ['GET','POST'])
@login_required
def nlp():
    user = current_user
    title = 'NLP'
    header = 'NLP Sandbox'
    form = NlpForm()

    d = {}
    if form.validate_on_submit():
        sentence = form.sentence.data
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        types = {}
        for token in tagged:
            if token[1] not in types.keys():
                types[token[1]] = [token[0]]
            else:
                types[token[1]].append(token[0])

        nounTags = []
        for tag in types.keys():
            if tag[0:2] == 'NN' or tag in ['PRP', 'JJ', 'DT']:
                nounTags.append(tag)

        verbTags = []
        for tag in types.keys():
            if tag[0:2] == 'VB' or tag in []:
                verbTags.append(tag)

        # Break up into parts
        parts = []
        parts.append([])
        switch = 'verb'

        for token in tagged:
            if token[0] == '.':
                parts[len(parts)-1].append(token)
                parts.append([])
                switch = 'verb'
            elif token[1] == 'IN':
                parts.append([])
                parts[len(parts)-1].append(token)
                switch = 'verb'
            else:
                checkList = nounTags if switch == 'noun' else verbTags

                if token[1] not in checkList:
                    parts[len(parts)-1].append(token)
                else:
                    parts.append([])
                    switch = 'noun' if switch == 'verb' else 'verb'
                    parts[len(parts)-1].append(token)

        metaParts = []
        switch = 'verb'
        metaParts.append([])
        for part in parts:
            if len(part) > 0:
                if switch == 'verb':
                    for token in part:
                        if token[1] in verbTags:
                            metaParts.append([])
                            switch = 'notverb'
                        index = len(metaParts)-1 if len(metaParts) > 0 else 0
                        metaParts[index].append(part)
                        break
                else:
                    for token in part:
                        if token[1] not in verbTags:
                            metaParts.append([])
                            switch = 'verb'
                        index = len(metaParts)-1 if len(metaParts) > 0 else 0
                        metaParts[index].append(part)
                        break

                if part[len(part)-1][0] == '.':
                    switch = 'notverb'



        subjects = ', '.join([token for token, tag in tagged if tag in nounTags])
        verbs = ', '.join([token for token, tag in tagged if tag in verbTags])


        d['sentence'] = sentence
        d['tokens'] = tokens
        d['tagged'] = tagged
        d['types'] = types
        d['nounTags'] = nounTags
        d['verbTags'] = verbTags
        d['subjects'] = subjects
        d['verbs'] = verbs
        d['parts'] = parts
        d['metaParts'] = metaParts


    return render_template('nlp.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form,
                           d = d
    )

@app.route('/nlpnew', methods = ['GET','POST'])
@login_required
def nlpnew():
    user = current_user
    title = 'NLP'
    header = 'NLP Sandbox'
    form = NlpForm()

    text = False

    if form.validate_on_submit():
        text = Text(form.sentence.data)


    return render_template('nlpnew.html',
                           user = user,
                           title = title,
                           header = header,
                           form = form,
                           text = text
    )