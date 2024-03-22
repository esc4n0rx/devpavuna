import os
import pytest
from flask_testing import TestCase
from app import app

class MyTest(TestCase):

    def create_app(self):
        
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  
        return app

    def setUp(self):
      
        db.create_all()

    def tearDown(self):
        
        db.session.remove()
        db.drop_all()


def test_example():
    assert True 
