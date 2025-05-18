import motor, asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME, SHORTLINK_API, SHORTLINK_URL
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from config import *

default_verify = {
    'is_verified': False,
    'verified_time': 0,  # Keep as integer
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': 0,  # Change to integer to match default_verify
            'verify_token': "",
            'link': ""
        }
    }

class rohit:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.user_data = self.database['users']
        self.sex_data = self.database['sex']
        self.banned_user_data = self.database['banned_user']
        self.autho_user_data = self.database['autho_user']
        self.del_timer_data = self.database['del_timer']
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        self.start_pics = self.database['start_pics']  
        self.force_pics = self.database['force_pics']

    async def initialize_shortlink_config(self):
        """Initialize shortlink_config with default values if not set."""
        existing_config = await self.shortlink_config.find_one({'_id': 'config'})
        if not existing_config:
            await self.shortlink_config.insert_one({
                '_id': 'config',
                'api': SHORTLINK_API,
                'url': SHORTLINK_URL
            })
            logging.info("Initialized default shortlink config in database.")

    async def initialize_tutorial_config(self):
        """Initialize tutorial_config with default TUT_VID if not set."""
        existing_config = await self.tutorial_config.find_one({'_id': 'config'})
        if not existing_config:
            await self.tutorial_config.insert_one({
                '_id': 'config',
                'tut_vid': TUT_VID
            })
            logging.info("Initialized default tutorial config in database.")

    # USER DATA
    async def present_user(self, user_id: int):
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        await self.user_data.insert_one({'_id': user_id})
        return

    async def full_userbase(self):
        user_docs = await self.user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in user_docs]
        return user_ids

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})
        return

    # ADMIN DATA
    async def admin_exist(self, admin_id: int):
        found = await self.admins_data.find_one({'_id': admin_id})
        return bool(found)

    async def add_admin(self, admin_id: int):
        if not await self.admin_exist(admin_id):
            await self.admins_data.insert_one({'_id': admin_id})
            return

    async def del_admin(self, admin_id: int):
        if await self.admin_exist(admin_id):
            await self.admins_data.delete_one({'_id': admin_id})
            return

    async def get_all_admins(self):
        users_docs = await self.admins_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids

    # BAN USER DATA
    async def ban_user_exist(self, user_id: int):
        found = await self.banned_user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_ban_user(self, user_id: int):
        if not await self.ban_user_exist(user_id):
            await self.banned_user_data.insert_one({'_id': user_id})
            return

    async def del_ban_user(self, user_id: int):
        if await self.ban_user_exist(user_id):
            await self.banned_user_data.delete_one({'_id': user_id})
            return

    async def get_ban_users(self):
        users_docs = await self.banned_user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids

    # AUTO DELETE TIMER SETTINGS
    async def set_del_timer(self, value: int):        
        existing = await self.del_timer_data.find_one({})
        if existing:
            await self.del_timer_data.update_one({}, {'$set': {'value': value}})
        else:
            await self.del_timer_data.insert_one({'value': value})

    async def get_del_timer(self):
        data = await self.del_timer_data.find_one({})
        if data:
            return data.get('value', 600)
        return 0

    # CHANNEL MANAGEMENT
    async def channel_exist(self, channel_id: int):
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id})
            return

    async def rem_channel(self, channel_id: int):
        if await self.channel_exist(channel_id):
            await self.fsub_data.delete_one({'_id': channel_id})
            return

    async def show_channels(self):
        channel_docs = await self.fsub_data.find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids
    
    async def get_channel_mode(self, channel_id: int):
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    async def set_channel_mode(self, channel_id: int, mode: str):
        await self.fsub_data.update_one(
            {'_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )

    # REQUEST FORCE-SUB MANAGEMENT
    async def req_user(self, channel_id: int, user_id: int):
        try:
            await self.rqst_fsub_Channel_data.update_one(
                {'_id': int(channel_id)},
                {'$addToSet': {'user_ids': int(user_id)}},
                upsert=True
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to add user to request list: {e}")

    async def del_req_user(self, channel_id: int, user_id: int):
        await self.rqst_fsub_Channel_data.update_one(
            {'_id': channel_id}, 
            {'$pull': {'user_ids': user_id}}
        )

    async def req_user_exist(self, channel_id: int, user_id: int):
        try:
            found = await self.rqst_fsub_Channel_data.find_one({
                '_id': int(channel_id),
                'user_ids': int(user_id)
            })
            return bool(found)
        except Exception as e:
            print(f"[DB ERROR] Failed to check request list: {e}")
            return False  

    async def reqChannel_exist(self, channel_id: int):
        channel_ids = await self.show_channels()
        return channel_id in channel_ids

    # VERIFICATION MANAGEMENT
    async def db_verify_status(self, user_id):
        user = await self.user_data.find_one({'_id': user_id})
        if user:
            return user.get('verify_status', default_verify)
        return default_verify

    async def db_update_verify_status(self, user_id, verify):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

    async def get_verify_status(self, user_id):
        verify = await self.db_verify_status(user_id)
        return verify

    async def update_verify_status(self, user_id, verify_token="", is_verified=False, verified_time=0, link=""):
        current = await self.db_verify_status(user_id)
        current['verify_token'] = verify_token
        current['is_verified'] = is_verified
        current['verified_time'] = verified_time
        current['link'] = link
        await self.db_update_verify_status(user_id, current)

    async def set_verify_count(self, user_id: int, count: int):
        await self.sex_data.update_one({'_id': user_id}, {'$set': {'verify_count': count}}, upsert=True)

    async def get_verify_count(self, user_id: int):
        user = await self.sex_data.find_one({'_id': user_id})
        return user.get('verify_count', 0) if user else 0

    async def reset_all_verify_counts(self):
        await self.sex_data.update_many({}, {'$set': {'verify_count': 0}})

    async def get_total_verify_count(self):
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$verify_count"}}}]
        result = await self.sex_data.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0

    # SHORTLINK CONFIG MANAGEMENT
    async def set_shortlink_config(self, api: str, url: str):
        await self.shortlink_config.update_one(
            {'_id': 'config'},
            {'$set': {'api': api, 'url': url}},
            upsert=True
        )

    async def get_shortlink_config(self):
        config = await self.shortlink_config.find_one({'_id': 'config'})
        # If no config exists, return defaults from config.py
        return config if config else {'api': SHORTLINK_API, 'url': SHORTLINK_URL}

    # TUTORIAL VIDEO CONFIG MANAGEMENT
    async def set_tutorial_video(self, tut_vid: str):
        await self.tutorial_config.update_one(
            {'_id': 'config'},
            {'$set': {'tut_vid': tut_vid}},
            upsert=True
        )

    async def get_tutorial_video(self):
        config = await self.tutorial_config.find_one({'_id': 'config'})
        return config.get('tut_vid', TUT_VID) if config else TUT_VID

# START PHOTOS MANAGEMENT
    async def add_start_pics(self, url: str):
        photo_data = {
            "url": url
        }
        await self.start_pics.insert_one(photo_data)

    async def get_start_pics(self):
        photos = await self.start_pics.find().to_list(length=None)
        return photos

    async def delete_start_pics(self, photo_id: str):
        await self.start_pics.delete_one({"_id": ObjectId(photo_id)})

    # FORCE PHOTOS MANAGEMENT
    async def add_force_pics(self, url: str):
        photo_data = {
            "url": url
        }
        await self.force_pics.insert_one(photo_data)

    async def get_force_pics(self):
        photos = await self.force_pics.find().to_list(length=None)
        return photos

    async def delete_force_pics(self, photo_id: str):
        await self.force_pics.delete_one({"_id": ObjectId(photo_id)})
    


db = rohit(DB_URI, DB_NAME)