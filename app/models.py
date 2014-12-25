from app import db
import datetime

ROLE_USER = 0
ROLE_ADMIN = 1

# ---------------- Main user class -----------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(200))
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
    meals = db.relationship('Meal', backref = 'user', lazy = 'dynamic')


    # Needed for flask-login
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User {username}>'.format(username = self.username)

# ----------------- Blog post class ----------------------
# Can use raw HTML in the content field - template turns off autoescape for the content

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default = datetime.datetime.now())
    content = db.Column(db.UnicodeText())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {title} by {author}>'.format(title = self.title, author = self.author)

# ---------------- Item classes ----------------

# Many-to-many class linking PurchasedItem to Meal
meal_to_item = db.Table('meal_to_item',
    db.Column('id', db.Integer, primary_key = True),
    db.Column('meal_id', db.Integer, db.ForeignKey('meal.id')),
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'))
)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    label = db.Column(db.String(64), unique = True)
    cost = db.Column(db.Numeric(9,2))
    volume = db.Column(db.Integer)
    increment = db.Column(db.String(64))

    def __repr__(self):
        return '<Item {label}, costing {cost}'.format(label = self.label, cost = self.cost)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    label = db.Column(db.String(64), unique = True)
    minutes = db.Column(db.Integer)
    recipe = db.Column(db.UnicodeText())
    items = db.relationship('Item', secondary=meal_to_item,
                            backref = db.backref('meals'), lazy = 'dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Meal {label}'.format(label = self.label)

    def total_cost(self):
        total_cost = 0
        for item in self.items:
            total_cost += item.cost

        return total_cost

    def item_count(self):
        item_list = list()

        for item in self.items:
            item_list += item

        return len(item_list)