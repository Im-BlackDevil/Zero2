import asyncio
import os
import random
import sys
import re
import string 
import string as rohit
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    id = message.from_user.id
    

    # Check if user is banned
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    # ✅ Check Force Subscription
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # File auto-delete time in seconds
    FILE_AUTO_DELETE = await db.get_del_timer()

    # Add user if not already present
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    # Fetch all start sub pictures from the database
    start_pics = await db.get_start_pics()
    if start_pics:
        # Randomly select one image from the list
        start_pic = random.choice(start_pics)['url']
    else:
        start_pic = START_PIC  # Fallback to default if no photos in DB

    # Handle normal message flow
    text = message.text

    if len(text) > 7:
        try:
            basic = text.split(" ", 1)[1]
            if basic.startswith("yu3elk"):
                base64_string = basic[6:-1]
            else:
                base64_string = basic

            # Removed the short_url check, directly process the base64 string
        except Exception as e:
            print(f"Error processing start payload: {e}")

        string = await decode(base64_string)
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return

        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>Please wait...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        codeflix_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass

        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"<b>Tʜɪs Fɪʟᴇ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ  {get_exp_time(FILE_AUTO_DELETE)}. Pʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>"
            )

            await asyncio.sleep(FILE_AUTO_DELETE)

            for snt_msg in codeflix_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")

            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                ) if reload_url else None

                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification with 'Get File Again' button: {e}")
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/Infinix_Adult")],
                [
                    InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                    InlineKeyboardButton('ʜᴇʟᴘ •', callback_data="help")
                ]
            ]
        )
        await message.reply_photo(
            photo=start_pic,  # Use the dynamically selected start_pic
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            message_effect_id=5104841245755180586  # 🔥
        )
        return

#=====================================================================================#

# Create a global dictionary to store chat data
chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    """Ultra-optimized version with batch processing - Fixed version"""
    user_id = message.from_user.id
    
    # Send checking subscription message
    temp_msg = await message.reply("<b><i>Checking Subscription...</i></b>")
    
    try:
        # Get all channels from database
        all_channels_data = await db.show_channels()
        
        if not all_channels_data:
            return
        
        # Handle different return formats from db.show_channels()
        channels_to_process = []
        
        # Check if the data is a list of tuples or just chat_ids
        for item in all_channels_data:
            if isinstance(item, tuple) and len(item) >= 2:
                # Data format: (chat_id, mode)
                chat_id, mode = item[0], item[1]
                channels_to_process.append((chat_id, mode))
            elif isinstance(item, (int, str)):
                # Data format: just chat_id, need to fetch mode separately
                chat_id = int(item)
                mode = await db.get_channel_mode(chat_id)
                channels_to_process.append((chat_id, mode))
            else:
                # Try to handle as dict or other format
                try:
                    if hasattr(item, 'get'):
                        chat_id = item.get('chat_id') or item.get('id')
                        mode = item.get('mode', 'off')
                    else:
                        chat_id = int(item)
                        mode = await db.get_channel_mode(chat_id)
                    channels_to_process.append((chat_id, mode))
                except Exception as e:
                    print(f"Error processing channel item {item}: {e}")
                    continue
        
        if not channels_to_process:
            return
        
        # Batch process subscription checks
        subscription_tasks = [
            is_sub(client, user_id, chat_id) 
            for chat_id, _ in channels_to_process
        ]
        
        subscription_results = await asyncio.gather(*subscription_tasks, return_exceptions=True)
        
        # Filter non-subscribed channels
        non_subscribed = [
            (chat_id, mode) for (chat_id, mode), is_subscribed in zip(channels_to_process, subscription_results)
            if not isinstance(is_subscribed, Exception) and not is_subscribed
        ]
        
        # If user is subscribed to all channels, delete temp message and return
        if not non_subscribed:
            await temp_msg.delete()
            return
        
        # Batch fetch chat data for non-subscribed channels
        chat_data_tasks = []
        for chat_id, mode in non_subscribed:
            if chat_id not in chat_data_cache:
                chat_data_tasks.append(client.get_chat(chat_id))
            else:
                chat_data_tasks.append(asyncio.create_task(async_return(chat_data_cache[chat_id])))
        
        chat_data_results = await asyncio.gather(*chat_data_tasks, return_exceptions=True)
        
        # Update cache and build buttons
        buttons = []
        for (chat_id, mode), chat_data in zip(non_subscribed, chat_data_results):
            if isinstance(chat_data, Exception):
                print(f"Error fetching chat data for {chat_id}: {chat_data}")
                continue
                
            # Update cache
            chat_data_cache[chat_id] = chat_data
            
            # Generate button
            try:
                name = chat_data.title
                
                if mode == "on" and not chat_data.username:
                    invite = await client.create_chat_invite_link(
                        chat_id=chat_id,
                        creates_join_request=True,
                        expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                    )
                    link = invite.invite_link
                else:
                    if chat_data.username:
                        link = f"https://t.me/{chat_data.username}"
                    else:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                
                buttons.append([InlineKeyboardButton(text=name, url=link)])
            except Exception as e:
                print(f"Error creating button for chat {chat_id}: {e}")
        
        # Add retry button
        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except (IndexError, AttributeError):
            pass

        # Get force pic (consider caching this too)
        force_pics = await db.get_force_pics()
        force_pic_url = random.choice(force_pics)["url"] if force_pics else FORCE_PIC

        # Send final message
        await message.reply_photo(
            photo=force_pic_url,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        
        # Delete the temporary message after sending force sub message
        await temp_msg.delete()
        
    except Exception as e:
        print(f"Final Error in not_joined: {e}")
        await temp_msg.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @Im_Sukuna02</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )

async def async_return(value):
    """Helper function to return cached values as async tasks"""
    return value

# Alternative simpler version if the above still has issues
async def not_joined_simple(client: Client, message: Message):
    """Simpler version that handles database format issues"""
    user_id = message.from_user.id
    buttons = []
    
    # Send checking subscription message
    temp_msg = await message.reply("<b><i>Checking Subscription...</i></b>")
    
    try:
        # Get all channels from database
        all_channels_data = await db.show_channels()
        
        if not all_channels_data:
            return
        
        # Process each channel individually to avoid unpacking errors
        for item in all_channels_data:
            try:
                # Handle different possible formats
                if isinstance(item, tuple):
                    chat_id = item[0]
                    mode = item[1] if len(item) > 1 else await db.get_channel_mode(chat_id)
                elif isinstance(item, (int, str)):
                    chat_id = int(item)
                    mode = await db.get_channel_mode(chat_id)
                else:
                    print(f"Unexpected item format: {item}")
                    continue
                
                # Check subscription
                if await is_sub(client, user_id, chat_id):
                    continue
                
                # Get chat data from cache or fetch it
                if chat_id in chat_data_cache:
                    data = chat_data_cache[chat_id]
                else:
                    data = await client.get_chat(chat_id)
                    chat_data_cache[chat_id] = data
                
                name = data.title
                
                # Generate proper invite link based on the mode
                if mode == "on" and not data.username:
                    invite = await client.create_chat_invite_link(
                        chat_id=chat_id,
                        creates_join_request=True,
                        expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                    )
                    link = invite.invite_link
                else:
                    if data.username:
                        link = f"https://t.me/{data.username}"
                    else:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                
                buttons.append([InlineKeyboardButton(text=name, url=link)])
                
            except Exception as e:
                print(f"Error processing channel {item}: {e}")
                continue
        
        # If user is subscribed to all channels, delete temp message and return
        if not buttons:
            await temp_msg.delete()
            return
        
        # Add retry button
        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except (IndexError, AttributeError):
            pass

        # Get force pic
        force_pics = await db.get_force_pics()
        force_pic_url = random.choice(force_pics)["url"] if force_pics else FORCE_PIC

        # Send final message
        await message.reply_photo(
            photo=force_pic_url,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        
        # Delete the temporary message after sending force sub message
        await temp_msg.delete()
        
    except Exception as e:
        print(f"Final Error in not_joined_simple: {e}")
        await temp_msg.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @Im_Sukuna02</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )
#=====================================================================================##


#=====================================================================================##

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"Tᴏᴛᴀʟ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴋᴇɴs ᴛᴏᴅᴀʏ: <b>{total}</b>")


#=====================================================================================##

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data = "close")]])
    await message.reply(text=CMD_TXT, reply_markup = reply_markup, quote= True)