from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField, PasswordField, FileField, SelectField, RadioField
from wtforms.validators import Required, EqualTo

# ---------- User management forms ------------

class LoginForm(Form):
    email = TextField('email', validators = [Required()])
    password = PasswordField('password', validators = [Required()])

class CreateUserForm(Form):
    nickname = TextField('username', validators = [Required()])
    email = TextField('email', validators = [Required()])
    password = PasswordField('password', validators = [Required()])
    confirm = PasswordField('confirm', validators = [Required(), EqualTo('confirm', message="Passwords don't match")])
    is_admin = BooleanField('is_admin')

# -------------- Blog post management forms --------------------

class AddPostForm(Form):
    title = TextField('title', validators = [Required()])
    content = TextAreaField('content')

class EditPostForm(Form):
    title = TextField('title', validators = [Required()])
    content = TextAreaField('content')
    update_ts = BooleanField('update_ts')

# ---------------- SuperModeler -------------------

class DataUploadForm(Form):
    datafile = FileField('datafile')
    delimiter = RadioField('delimiter', choices=[('comma', 'Comma'),('tab','Tab')], validators=[Required()])
    y = SelectField('y', choices=[('nofile','---')])

    delimiter_translator = {'comma':',',
                            'tab':'\t'}

# ---------------- Food planner --------------------
class AddFoodItemForm(Form):
    increment_choices = [('oz', 'Oz.'),('cups','Cups'),('items','Individual Item(s)')]

    label = TextField('label', validators = [Required()])
    cost = TextField('cost', validators = [Required()])
    volume = TextField('volume', validators = [Required()])
    increment = RadioField('delimiter', choices=increment_choices, validators=[Required()])

class AddMealForm(Form):
    label = TextField('label', validators = [Required()])
    minutes = TextField('minutes')
    recipe = TextAreaField('recipe')

class NlpForm(Form):
    sentence = TextAreaField('sentence')
