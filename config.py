import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'mysql://root:@localhost/ungertime'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

CSRF_ENABLED = True
SECRET_KEY = 'super-secret-password'

ALLOWED_EXTENSIONS = ['csv']
UPLOAD_FOLDER = 'uploads'