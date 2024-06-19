# import slack

import os

from pathlib import Path

from dotenv import load_dotenv

from slack_sdk import WebClient

from flask import Flask, request, Response, jsonify

import requests

from slackeventsapi import SlackEventAdapter

from slack_sdk.errors import SlackApiError

import certifi
import ssl



#############################################################
# Global variables
#############################################################

message_counts = {}
users_store = {}



#############################################################



#############################################################

#Initializing connection with Slack API

#############################################################




# load the .env file with token and signing secret

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)

slack_token = os.environ['SLACK_TOKEN']

signing_secret = os.environ['SIGNING_SECRET']






#initialize web server and event handler

app = Flask(__name__)

slack_event_adapter = SlackEventAdapter(signing_secret,'/slack/events', app)



# # Handle the Slack URL verification challenge
# @app.route("/slack/events", methods=["POST"])
# def slack_events():
#     if request.headers['Content-Type'] == 'application/json':
#         data = request.get_json()
#         if 'challenge' in data:
#             return jsonify({"challenge": data['challenge']})
#     return "OK"


# initialize the slack client

ssl_context = ssl.create_default_context(cafile=certifi.where())

client = WebClient(token=slack_token, ssl = ssl_context)

BOT_ID = client.api_call("auth.test")['user_id']




###############################################################






###############################################################

# Bot responses to events

###############################################################




# Response to a new message in a channel


@slack_event_adapter.on('message')

def message(payload):

   event = payload.get('event', {})

   channel_id = event.get('channel')

   user_id = event.get('user')

   response = client.conversations_info(channel=channel_id)

   channel_name = response['channel']['name']

   if not channel_name.startswith('d-'):

        return

   if BOT_ID != user_id:

       if user_id in message_counts:

           message_counts[user_id] += 1

       else:

           message_counts[user_id] = 1




# Response to the creation of a new digital channel (-d)

@slack_event_adapter.on('channel_created')

def channel_created(event_data):

   event = event_data['event']

   channel = event['channel']

   channel_name = channel['name']

   creator_id = channel['creator']


   if channel_name.startswith('d-'):

       try:

           client.conversations_join(channel=channel['id'])

           response_url = request.form.get('response_url')
           response_data = {
                "response_type": "ephemeral", 
                "text": "Welcome to your new Digital Channel! Use /digital help for more info"
            }

           requests.post(response_url, json=response_data)

       except SlackApiError as e:

           if e.response['error'] == 'not_in_channel':

               try:

                   client.chat_postMessage(

                       channel=creator_id,

                       text=f"Hi there! I noticed you created a new Digital channel named {channel_name}. "

                            f"I'd love to join and assist. Please invite me to the channel! Type /digital help for more info."

                   )

               except SlackApiError as e:

                   print(f"Error sending message to creator: {e.response['error']}")

           else:

               print(f"Error joining channel or sending message: {e.response['error']}")




            




###############################################################

   




###############################################################

# Functions which carry out the commands

###############################################################




# helper function for list channels

def get_channel_owner(user_id):

       user_info = client.users_info(user=user_id)

       return user_info['user']['real_name']




# helper function for list channels

def get_channel_info(channel_id):

       channel_info = client.conversations_info(channel=channel_id)

       return channel_info['channel']



# list channels

def digital_channels():


   public_channels = client.conversations_list(types="public_channel")['channels']

   public_channels = [channel for channel in public_channels if channel['name'].startswith('d-')]


   private_channels = client.conversations_list(types="private_channel")['channels']

   private_channels = [channel for channel in private_channels if channel['name'].startswith('d-')]


   message_text = "*Digital Channels:*\n"


   for channel in public_channels + private_channels:

       channel_info = get_channel_info(channel['id'])

       if channel_info:

           owner = get_channel_owner(channel_info['creator'])

           description = channel_info['purpose']['value']

           if description == "":

                description = "No description available"

           message_text += f"*• {channel_info['name']}*\n    - Owner: {owner}\n    - Description: {description}\n\n"

       else:

           message_text += f"*• {channel['name']}*\n    - Owner: Unknown\n    - Description: No description available\n\n"


   response_url = request.form.get('response_url')
   response_data = {
        "response_type": "ephemeral", 
        "text": message_text
    }

   requests.post(response_url, json=response_data)

   return Response(), 200




# message count

def message_count():

   data = request.form

   user_id = data.get('user_id')

   message_count = message_counts.get(user_id, 0)

   response_url = request.form.get('response_url')
   response_data = {
        "response_type": "ephemeral", 
        "text":  f"You sent {message_count} message(s) in Digital channels!"
    }

   requests.post(response_url, json=response_data)

   return Response(), 200





# help

def help(commands):

   message = "Hello! The Digital Slackbot helps to automate daily functions and display important resources for the Digital team. Use me by using /digital [command]. Here are the available commands: \n\n "

   for command in commands:

         message += f"*• {command}*\n    - {commands[command]}\n\n"


   response_url = request.form.get('response_url')
   response_data = {
        "response_type": "ephemeral", 
        "text": message
    }

   requests.post(response_url, json=response_data)

   return Response(), 200




# list user function

def list_users():

    data = request.form
    channel_id = data.get('channel_id')

    channel_info = client.conversations_info(channel=channel_id)
    channel_name = channel_info['channel']['name']

    if not channel_name.startswith('d-'):
        message_text = "This command can only be used in digital channels"
        
        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": message_text
        }

        requests.post(response_url, json=response_data)
        return Response(), 200
   
   
    fetch_and_save_users()

    try:
        response = client.conversations_members(channel=channel_id)
        user_ids = response['members']

        user_names = []
        bot_names = []

        for user_id in user_ids:
            user = users_store.get(user_id)
            if user:
                if user.get('is_bot', False):
                    bot_names.append(user['real_name'])
                else:
                    user_names.append(user['real_name'])

        user_list = "\n".join(user_names)
        bot_list = "\n".join(bot_names)
        message_text = f"*Bots in this channel:*\n{bot_list}\n\n*Users in this channel:*\n{user_list}"
        
        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": message_text
        }

        requests.post(response_url, json=response_data)

    except SlackApiError as e:
        error_message = f"Error fetching users: {e.response['error']}"
       
        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": error_message
        }

        requests.post(response_url, json=response_data)

    return Response(), 200


# helper function for list user

def fetch_and_save_users():
    try: 
        result = client.users_list()
        save_users(result["members"])

    except SlackApiError as e:
        logger.error("Error fetching users: {}".format(e))

# helper function for list user

def save_users(users_array):
    for user in users_array:
        user_id = user["id"]
        users_store[user_id] = user





#check if user is in digital 
def check_digital(user_id):
    user_info = client.users_info(user=user_id)

    name = user_info['user']['real_name']
    name = 'Eddie Du Vall'
    target = 'https://www.wwt.com/api/corpsite/profiles?search=' + name
    response = requests.get(target)

    if response.status_code == 200:
        print('request successful')
        print(response.text)
        data_check = response.json()
        profiles = data_check.get('data', [])
        for profile in profiles:
            if (profile.get('fullName') == name and
                    ('SOL Digital Overhead' == profile.get('department', '') or 
                     'CS Digital Billable' == profile.get('department', '') or 
                     'SOL Digital SSA' == profile.get('department', ''))):
                return True
        return False
    else:
        print('request fail')
        return 404


# list bookmarks function

def list_bookmarks():
    data = request.form
    channel_id = data.get('channel_id')

    channel_info = client.conversations_info(channel=channel_id)
    channel_name = channel_info['channel']['name']

    if not channel_name.startswith('d-'):
        message_text = "This command can only be used in digital channels"
        
        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": message_text
        }

        requests.post(response_url, json=response_data)
        return Response(), 200
   

    try:
        # Fetch the list of bookmarks using the bookmarks.list API
        response = client.api_call("bookmarks.list", params={"channel_id": channel_id})
        if response.get("ok"):
            bookmarks = response['bookmarks']
            if bookmarks:
                message_text = "*Bookmarks in this channel:*\n"
                for bookmark in bookmarks:
                    message_text += f"*• {bookmark['title']}*\n    - Link: {bookmark['link']}\n\n"
            else:
                message_text = "No bookmarks found in this channel."
        else:
            message_text = f"Error fetching bookmarks: {response['error']}"

        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": message_text
        }

        requests.post(response_url, json=response_data)

        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": message_text
        }

        requests.post(response_url, json=response_data)


    except SlackApiError as e:
        error_message = f"Error fetching bookmarks: {e.response['error']}"
       
        response_url = request.form.get('response_url')
        response_data = {
                 "response_type": "ephemeral", 
                "text": error_message
        }

        requests.post(response_url, json=response_data)


    return Response(), 200





###############################################################








###############################################################

# handler for the /digital commands

###############################################################




commands = {'list channels': 'lists all public and private Digital channels',

            'message count': 'shows the number of messages you sent in Digital channels',

            'help': 'provides an overview and available commands of the Digital Slackbot',

            'users': 'shows the users that are in the channel',
            
            'list bookmarks': 'shows all bookmarks in the current channel'
            }




@app.route('/digital', methods = ['POST'])

def digital():

    data = request.form

    # check if user in Digital

    team = check_digital( data.get('user_id'))

    if team == 404:
         
        response_url = request.form.get('response_url')
        response_data = {
            "response_type": "ephemeral", 
            "text": "Error in verifying your current team"
        }

        requests.post(response_url, json=response_data)
        return Response(), 200

    if not team:
        response_url = request.form.get('response_url')
        response_data = {
            "response_type": "ephemeral", 
            "text": "Error in verifying your current team"
        }

        requests.post(response_url, json=response_data)
        return Response(), 200

    ############################

    command = data.get('text', '')

    if command == 'list channels':

         return digital_channels()

    elif command == 'message count':

         return message_count()

    elif command == 'help':

         return help(commands)
    
    elif command == 'users':

        return list_users()
    
    elif command == 'list bookmarks':

        return list_bookmarks()

    else:
         
         response_url = request.form.get('response_url')
         response_data = {
            "response_type": "ephemeral", 
            "text": "Not a valid command. Use ** /digital help ** for a list of available commands!"
         }

         return Response(), 200

    

###############################################################         






###############################################################




#keep debugger running, run web server if file is not imported

if __name__ == "__main__":

   app.run(debug=True, port = 8080)
