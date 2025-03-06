import json

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import re


class CloudData():
    def __init__(self) -> None:
        uri = "mongodb+srv://stat7008:E7keNsXtKH7EkBXk@cluster0.nx6bu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        # Create a new client and connect to the server
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            print("You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
        
        self.db = self.client['stat7008_database']
        
    # def test_get_data(self) -> dict:
    #     # Get the collection
    #     db = self.client['sample_mflix']
    #     collection = db["users"]
    #     # Get the first document
    #     data = collection.find_one({"name":"Ned Stark"})

    #     return data
    
    def _get_data(self, collection_name: str, query: dict) -> dict:
        # Get the collection
        collection = self.db[collection_name]
        # Get the first document

        data = collection.find_one(query)

        return data

    def _get_all_data(self, collection_name: str) -> list:
        collection = self.db[collection_name]
        all_documents = collection.find({})
        data = list(all_documents)
        return data
    
    def _insert_data(self, collection_name: str, data: dict) -> None:
        # Get the collection
        collection = self.db[collection_name]
        # Insert the data
        collection.insert_one(data)
    
    def get_settings(self) -> dict:
        data = self._get_data('settings', {"name":"settings"})
        return data['settings']
    
    def update_settings(self, settings: dict) -> None:
        assert len(settings) == 2
        assert "init_prompt" in settings
        assert "api_key" in settings

        db_settings = {"name":"settings",
                      "settings":settings}

        self.db['settings'].delete_one({"name":"settings"})
        self._insert_data('settings', db_settings)

    def get_user(self, user_name: str) -> dict:
        data = self._get_data('users', {"name":user_name})
        return data
    
    def get_all_users(self) -> list:
        data = self._get_all_data('users')
        return data
    
    def add_user(self, user: dict) -> list[bool, str]:
        assert len(user) == 3
        assert "name" in user
        assert "email" in user
        assert "password" in user
        if not  re.match(r"[^@]+@[^@]+\.[^@]+", user['email']):
            return [False, "Invalid email format"]
        if user['name'] == "" or user['email'] == "" or user['password'] == "":
            return [False, "Please fill in all fields"]
        if self.get_user(user['name']) is not None:
            return [False, "User_name already exists"]
        if self.get_user(user['email']) is not None:
            return [False, "User_email already exists"]
        self._insert_data('users', user)

        return [True, "User added successfully"]

    def delete_user(self, user_name: str) -> None:
        self.db['users'].delete_one({"name":user_name})

    def user_login(self, user_name: str, user_pwd: str) -> list[bool, str]:
        user = self.get_user(user_name)
        if user is None:
            return [False, "User not found"]
        if user['password'] != user_pwd:
            return [False, "Password incorrect"]
        return [True, "Login successful"]
    
    def forget_password(self, user_name: str, email:str) -> None:
        if user_name == "admin":
            return [False, "Cannot find admin password"]
        user = self.get_user(user_name)
        if user is None:
            return [False, "User not found"]
        if user['email'] != email:
            return [False, "Email incorrect"]
        return [True, f"Your password is {user['password']}"]


    def __del__(self) -> None:
        self.client.close()
        

    