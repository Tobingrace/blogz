from whoosh.qparser import QueryParser
from application import search_ix
from config import MAX_SEARCH_RESULTS

from flask import Flask, Response, render_template, flash, redirect, session, url_for, request, jsonify, g
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import datetime

from flask_sqlalchemy import get_debug_queries, Pagination
#######################################################################
### Importing the app and configurations over here ####################
#######################################################################
from application import app, db, login_manager, flask_bycrypt, google, oauth
from .forms import LoginForm, RegistrationForm, PostForm, SearchForm, EditForm
from .models import User, Post
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, DATABASE_QUERY_TIMEOUT
#######################################################################
################## End of Importing####################################
#######################################################################




########################################################################
#################### Begin Login/Logout Route ##########################
########################################################################
# LoginManger 
# https://flask-login.readthedocs.io/en/latest/
########################################################################
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('google_token', None)
    return redirect(url_for('login'))
########################################################################
#################### End Login/Logout Route ############################
########################################################################
@app.before_request
# @cache.cached(timeout=60)
def before_request():
    print(current_user)
    g.user = current_user
    print('G.User is:',g.user.is_authenticated)
    g.search_form = SearchForm()
    if g.user.is_authenticated:
        # keeping track of last logins
        g.user.last_seen = datetime.utcnow()
        print(g.user.last_seen)
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()

'''
@login_manager.user_loader
def load_user(session_token):
    return User.query.filter_by(session_token=session_token).first()
'''
########################################################################
#################### Begin After Requests Route ########################
########################################################################
# Means to notify if the queries are running long
########################################################################
@app.after_request
def after_request(response):
    if g.user.is_authenticated:
        print('G.User status after request:',g.user.is_authenticated)
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning(
                "SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" %
                (query.statement, query.parameters, query.duration,
                 query.context))
    return response
########################################################################
#################### End After Requests Route ########################
########################################################################




########################################################################
######################## Begin Error Routing ###########################
########################################################################
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')

# Handling specific errors
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
########################################################################
######################## End Internal Error Route ######################
########################################################################




########################################################################
######################## Begin Followed Route ##########################
########################################################################
@app.route('/followed', methods=['GET', 'POST'])
@app.route('/followed/<int:page>', methods=['GET', 'POST'])
@login_required
# @cache.cached(timeout=60)
def followed(page=1):
    form = PostForm()

    if request.method == 'POST':
        posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
        return render_template('followed.html',
                            title='Friends',
                            posts=posts, 
                            form=form)

    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('followed.html',
                            title='Friends',
                            posts=posts, 
                            form=form)
########################################################################
######################## End Followed Route ############################
########################################################################

@app.route('/pagefoldout.html')
def pagefoldout(page=1):
    if form.validate_on_submit():
        
        post = Post(author=g.user, title=form.title.data,
        content=form.content.data, timestamp=datetime.utcnow())
        db.session.add(post)
        db.session.commit()

        flash('Your post is now live!')
        writer = search_ix.writer()
        writer.add_document(id=str(post.post_id), content=post.content)
        writer.commit()
        flash('Your post is now indexed!')
        return redirect(url_for('index'))

    post = (db.session.query(Post).order_by(Post.timestamp.desc()).limit(50)).from_self()

    for p in post:
        app.logger.debug(p)


    if post is None:
        flash('Error: no posts returned.')
        return redirect(url_for('index'))
    posts = post.paginate(page, POSTS_PER_PAGE, False)
    
    return render_template('pagefoldout.html',
                        title='Home',
                        form=form,
                        posts=posts)




########################################################################
######################## Begin Index Route #############################
########################################################################
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
# @cache.cached(timeout=60)
def index(page=1):
    form = PostForm()
    
    if form.validate_on_submit():
        
        post = Post(author=g.user, title=form.title.data,
        content=form.content.data, timestamp=datetime.utcnow())
        db.session.add(post)
        db.session.commit()

        flash('Your post is now live!')
        writer = search_ix.writer()
        writer.add_document(id=str(post.post_id), content=post.content)
        writer.commit()
        flash('Your post is now indexed!')
        return redirect(url_for('index'))

    post = (db.session.query(Post).order_by(Post.timestamp.desc()).limit(50)).from_self()

    if post is None:
        flash('Error: no posts returned.')
        return redirect(url_for('index'))
    posts = post.paginate(page, POSTS_PER_PAGE, False)
    
    return render_template('index.html',
                        title='Home',
                        form=form,
                        posts=posts)
########################################################################
######################## End Index Route ###############################
########################################################################




########################################################################
######################## Begin Register Route ##########################
########################################################################
@app.route('/register', methods=['GET', 'POST'])
# @cache.cached(timeout=60)
def register():
    form = RegistrationForm()

    if request.method == 'POST':
        
        if form.validate_on_submit():
            
            if add_user_to_db(form):
                
                first = form.first.data

                flash('You are now registered '+ first, 'success')
                return redirect(url_for('login'))


            else:
                username = form.username.data

                flash( username + ', has already been taken please choose a different username', 'danger')
                return render_template('register.htlm', form=form)
        else:
            
            flash('Please correct the issues below, 1', 'danger')
            return render_template('register.html', form=form)
    else:
        return render_template('register.html', form=form)
########################################################################
#################### End Register Route ################################
########################################################################




########################################################################
######################## Begin Login Route #############################
########################################################################
@app.route('/login', methods=['GET', 'POST'])
# @cache.cached(timeout=60)
def login():
    form = LoginForm()

    if 'google_token' in session:
        me = google.get('userinfo')
    
    if request.method == 'GET':
        if g.user is not None and g.user.is_authenticated:
            app.logger.debug("Form has been loaded by:{}  Is the user logged in: {}".format(g.user.is_authenticated, g.user.is_authenticated))
            return redirect(url_for('index'))
        else:
            return render_template('login.html', form=form)

    if request.method == 'POST':
        
        app.logger.debug("Post request made by: {}  Is the user logged in: {}".format(g.user, g.user.is_authenticated))
        
        if form.validate_on_submit():
            app.logger.debug("Form validate by: {}  Is the user logged in: {}".format(g.user, g.user.is_authenticated))
            
            # Grabbing user input to validate if the user exists
            username = form.username.data
            candidate = form.password.data
            remember_me = form.remember_me.data
            
            # Check if the username exists
            user = User.query.filter_by(username=username).first()
            app.logger.debug("Form validate by: {}  Is the user logged in: {}".format(g.user, g.user.is_authenticated))
            
            # Validating at least one return (unique field should only be one)
            if user:
                app.logger.debug("Does User exist: {}  Is the user logged in: {}".format(g.user, g.user.is_authenticated))
                
                # Grabbing users hashed password from the database
                hashed_password = user.password
                
                # Validating password hash
                if flask_bycrypt.check_password_hash(hashed_password, candidate):
                    app.logger.debug("Did the password validate: {}  Is the user logged in: {}".format(current_user, g.user.is_authenticated))
                    login_user(user)


                    next = request.args.get('next')

                    return redirect(request.args.get('next') or url_for('index'))
                else:
                    flash('The password or username you entered is incorrect', 'danger')
                    return render_template('login.html', form=form)
            else:
                flash('There was an error with your login.  Please try again.', 'danger')
                return render_template('login.html', form=form)
        else:
            flash('Please correct the issues below.', 'danger')
            return render_template('login.html', form=form)
########################################################################
#################### End Login Route ###################################
########################################################################




########################################################################
#################### Begin Follow/Unfollow-->Users Route ###############
########################################################################
@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.'.format(username))
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!'.format(username))
        return redirect(url_for('user', username=username))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow {}s.'.format(username))
        return redirect(url_for('user', username=username))
    db.session.add(u)
    db.session.commit()
    flash('You are now following %(username)s!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.'.format(username))
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', username=username))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow %(username)s.'.format(username))
        return redirect(url_for('user', username=username))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following %(username)s.'.format(username))
    return redirect(url_for('user', username=username))
########################################################################
#################### End Follow/Unfollow-->Users Route #################
########################################################################




########################################################################
#################### Begin User-Version Home Page Profile Route ########
########################################################################
@app.route('/user/<username>')
@app.route('/user/<username>/<int:page>')
@login_required
def user(username, page=1):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User %s not found.' % username)
        return redirect(url_for('index'))
    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html',
                           user=user,
                           posts=posts)
########################################################################
#################### End User-Version Home Page Profile Route ##########
########################################################################




########################################################################
#################### Begin Edit Profile Route ##########################
########################################################################
@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        g.user.username = form.username.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.username.data = g.user.username
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)
########################################################################
#################### End Edit Profile Route ############################
########################################################################




########################################################################
#################### Begin Posts Route #################################
########################################################################
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get(id)
    if post is None:
        flash('Post not found.')
        return redirect(url_for('index'))
    if post.author.user_id != g.user.user_id:
        flash('You cannot delete this post.')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.')
    return redirect(url_for('index'))
########################################################################
#################### Delete Posts Route ################################
########################################################################




########################################################################
#################### Begin (Query)Search Routes ########################
########################################################################
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        flash('We have a problem huston!')
        return redirect(url_for('index'))

    return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route('/search_results/<query>')
@login_required
def search_results(query):
    qp = QueryParser('content', schema=search_ix.schema)
    q = qp.parse(query)
    with search_ix.searcher() as s:
        rs = s.search(q, limit=MAX_SEARCH_RESULTS)
        results = []
        if type(rs) is not None:
            for r in rs:
                results.append(Post.query.get(int(r['id'])))

    return render_template('search_results.html',
                           query=query,
                           results=results)
########################################################################
#################### End (Query)Search Route ###########################
########################################################################




########################################################################
#################### Start Process Functions ###########################
########################################################################
def add_user_to_db(form):
    
    first = form.first.data
    last = form.last.data
    username = form.username.data
    email = form.email.data
    password = flask_bycrypt.generate_password_hash(form.password.data).decode('utf-8')

    user = User.query.filter_by(username=username)

    if user.count() == 0:
        username = User.make_valid_username(username)
        username = User.make_unique_username(username)

        new_user = User()
        new_user.first = first
        new_user.last = last
        new_user.username = username
        new_user.email = email
        new_user.password = password

        db.session.add(new_user)
        db.session.commit()
        db.session.add(new_user.follow(new_user))
        db.session.commit()
        app.logger.debug("The user was successfully saved to the database.")

        return True

    return 
########################################################################
#################### End Process Functions #############################
########################################################################


@app.route('/g_login')
def g_login():
    return google.authorize(callback=url_for('authorized', _external=True))


@app.route('/login/authorized')
def authorized():
    error = False
    
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    response = me.data

    email = response['email']
    user = User.query.filter_by(email=email).first()

    if user:
        login_user(user)


        next = request.args.get('next')
        
        return redirect(request.args.get('next') or url_for('index'))

    else:
        
        new_user = User()
        
        try:
            first, last = response['name'].split(' ')
            picture = response['link']
            username = response['name'].strip(' ')

            new_user.first = first
            new_user.last = last
            new_user.avatar_link = picture
            
        except ValueError:
            error = True
            flash('Please remember to update your profile to include your name')

        if error:
            username = response['email']
        
        username = User.make_valid_username(username)
        username = User.make_unique_username(username)

        
        new_user.username = username
        new_user.email = email

        db.session.add(new_user)
        db.session.commit()
        db.session.add(new_user.follow(new_user))

        db.session.commit()

        login_user(new_user)

        next = request.args.get('next')

        flash("Welcome to Build-a-Blog.")
        return redirect(request.args.get('next') or url_for('index'))



@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')
