import os
import discord
import traceback
import logging
import re
import time

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

seen_emoji_long_id = os.getenv("SEEN_EMOJI_LONG_ID")
doodle_channel_id = int(os.getenv("DOODLE_CHANNEL_ID"))
doodle_seen_reaction = os.getenv("DOODLE_SEEN_REACTION")
notify_role_id = int(os.getenv("NOTIFY_ROLE_ID"))
client_token = os.getenv("DISCORD_CLIENT_TOKEN")

doodle_links = os.getenv("DOODLE_LINKS").split(',')

async def new_message_handler(message):
    if message.author == client.user:
        return
    if message.position is None:
        try:
            await thread_handler(message)
            await message.add_reaction(seen_emoji_long_id)
        except Exception:
            logging.error(traceback.format_exc())
    elif get_thread_name(message.content) == '[cd]':
        try:
            await message.add_reaction(seen_emoji_long_id)
        except Exception:
            logging.error(traceback.format_exc())
    time.sleep(0.5)
    await doodle_handler(message)
    await poll_handler(message)

async def doodle_handler(message):
    for doodle_link in doodle_links:
        if (doodle_link in message.content):
            channel = client.get_channel(doodle_channel_id)
            new_message = await channel.send(message.jump_url + '\n>>> ' + message.content)
            await new_message.add_reaction(doodle_seen_reaction)

async def poll_handler(message):
    options = re.findall(r'> - .+', message.content)
    for option in options:
        emoji = get_option_emoji(option)
        await message.add_reaction(emoji)

def get_option_emoji(option_string):
    emoji = option_string[4:].split()[0]
    if (emoji[0] == '<' and emoji[-1] == '>'):
        emoji = emoji[1:-1]
    return emoji

async def thread_handler(message):
    thread_name = get_thread_name(message.content)
    if (thread_name is not None) :
        thread = await message.create_thread(name = thread_name)
        await thread.send(f'<@&{notify_role_id}>\nreactions:')

async def reaction_change_handler(payload):
    if payload.user_id == client.user.id:
        return
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if message.position is None:
       await update_reaction_msg(message)

def get_thread_name(message_content):
    title = re.search(r'\[[^\]]*\]', message_content)
    return title.group(0) if title is not None else None

def reactions_to_str(reactions):
    message = "reactions:\n"
    for reaction in reactions:
        message += str(reaction.emoji) + ":" + str(reaction.count) + "    "
    return message

async def get_reaction_msg(message):
    thread = discord.utils.get(message.channel.threads, id = message.id)
    if thread is None:
        return
    messages = [message async for message in thread.history(limit=2, oldest_first=True)]
    if (len(messages) < 2 or messages[1].author != client.user):
        return None
    return messages[1]

async def update_reaction_msg(message):
    reactions = message.reactions
    reaction_msg = await get_reaction_msg(message)
    if reaction_msg is not None:
        reaction_msg_conent = reactions_to_str(reactions)
        await reaction_msg.edit(content=(f'<@&{notify_role_id}>\n' + reaction_msg_conent))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    await new_message_handler(message)

@client.event
async def on_raw_reaction_add(payload):
    await reaction_change_handler(payload)

@client.event
async def on_raw_reaction_remove(payload):
    await reaction_change_handler(payload)

client.run(client_token)
