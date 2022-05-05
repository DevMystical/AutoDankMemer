import discord, requests, json, time, random, string, asyncio, base64, os
from discord.ext import tasks

class LogType:
    INFO    = ("\033[0;1;97m",            "INFO",    0)
    DIED    = ("\033[1;38;2;255;89;94m",  "DIED",    0)
    BUY     = ("\033[1;38;2;25;130;196m", "BUY",     1)
    EARN    = ("\033[1;38;2;138;201;38m", "EARN",    0)
    ERROR   = ("\033[1;38;5;196m",        "WARN",    0)
    ROBBERY = ("\033[1;38;5;196m",        "ROB",     1)
    SUMMARY = ("\033[0;1;97m",            "SUMMARY", 0)

def log(message, log_type):
    print(f"\033[0;1;97m [ {log_type[0]}{log_type[1]}\033[0;97m {' '*log_type[2]}] \033[0;97m{message}\033[0m")

log("DankMemerBot - By Mystical (2022)", LogType.INFO)

def get_guild_id(channel_id):
    try:
        return requests.get(f"https://discord.com/api/v9/channels/{channel_id}", headers={"Authorization": f"Bot {BOT_TOKEN}"}).json()["guild_id"]
    except KeyError:
        return None

def get_my_information(token):
    try:
        data = requests.get(f"https://discord.com/api/v9/users/@me", headers={"Authorization": token}).json()
        return data["id"], data["username"], data["discriminator"]
    except KeyError:
        return None

try:
    config = json.load(open("BotConfig.json"))
except:
    log("Error - BotConfig.json was not found or is invalid.", LogType.ERROR)
    exit()

BOT_TOKEN = config["BOT_TOKEN"]
USER_TOKEN = config["USER_TOKEN"]
CHANNEL_ID = config["CHANNEL_ID"]
GUILD_ID = get_guild_id(CHANNEL_ID)
MY_ID, NAME, MY_DISCRIM = get_my_information(USER_TOKEN)
AUTHORIZED_USERS = config["AUTHORIZED_USERS"] + [MY_ID]
DANK_MEMER_ID = 270904126974590976

if GUILD_ID is None:
    log("That channel does not exist or is not accessible.", LogType.ERROR)
    exit()
if MY_ID is None or NAME is None:
    log("That token is invalid or is not reachable.", LogType.ERROR)
    exit()

b64 = lambda s: base64.b64decode(s).decode('utf-8')
if not "trivia.json" in os.listdir():
    TRIVIA_DATA = None
    log("File trivia.json was not found, random trivia answers will be selected.", LogType.INFO)
else:
    TRIVIA_DATA = {}
    with open("trivia.json") as f:
        trivia = json.load(f)
    for category, question_list in trivia.items():
        cat_name = b64(category)
        if not cat_name in TRIVIA_DATA:
            TRIVIA_DATA[cat_name] = {}
        for question in question_list:
            TRIVIA_DATA[cat_name][b64(question["question"])] = b64(question["answer"])

COMMANDS = {"hl": 32, "beg": 35, "search": 30, "postmemes": 40, "dig": 40, "fish": 40, "hunt": 40, "sell": 300, "crime": 45, "trivia": 20, "dep max": 300, "work": 3660}
CRIME_DEATH_CHUNKS = ["shot", "killed", "choked to death", "MURDERED", "died", "death penalty"]
SEARCH_DEATH_CHUNKS = ["killing", "died", "shot", "killed", "mutant", "catfished", "and bit you.", "parked", "infectious disease ward", 
    "sent chills down your spine", "burned to death", "TO DEATH", "hit by a car LOL", "Epsteined"]
SEARCH_PRIORITY = ["coat", "mailbox", "pantry", "shoe", "grass", "who asked", "pocket", "sink", "dresser", "laundromat", "bus",
    "basement", "car", "fridge", "washer", "vacuum"]
STEAL_FLAGS = [f"pls rob {NAME}#{MY_DISCRIM}", f"pls rob <@{MY_ID}>", f"pls steal {NAME}#{MY_DISCRIM}", f"pls steal <@{MY_ID}>",
    f"pls ripoff {NAME}#{MY_DISCRIM}", f"pls ripoff <@{MY_ID}>"]

def post_message(content):
    res = requests.post(f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages", headers={"Authorization": USER_TOKEN}, json={"content": content})
    return res.json()["id"] if "id" in res.json() else False

def get_label_mapping_and_list(data):
    labels, label_list = {}, []
    for component in data["components"][0]["components"]:
        labels[component["label"]] = component["custom_id"]
        label_list.append(component["label"])
    return labels, label_list

def get_ideal_search_id(data):
    labels, label_list = get_label_mapping_and_list(data)
    to_delete = []
    for label in labels.keys():
        if not label in SEARCH_PRIORITY:
            to_delete.append(label)
    for label in to_delete:
        del labels[label]
        label_list.remove(label)
    if len(label_list) == 0:
        return None
    selected = 100
    for label in label_list:
        if SEARCH_PRIORITY.index(label) < selected:
            selected = SEARCH_PRIORITY.index(label)
    return labels[SEARCH_PRIORITY[selected]]

def get_correct_trivia_id(data, question, category):
    labels, label_list = get_label_mapping_and_list(data)
    if not (category in TRIVIA_DATA and question in TRIVIA_DATA[category]):
        return None
    correct_answer = TRIVIA_DATA[category][question]
    if correct_answer in label_list:
        return labels[correct_answer]
    else:
        return None
    
class BotMessage:
    def __init__(self, message):
        self.message = message
        self.message_id = message.id
        self.load_message_data = False
        self.command_name = None
        self.loaded_data_dict = None
        self.dumped_data = None

        try:
            if message.embeds[0].author.name in [NAME + "'s high-low game", NAME + "'s winning high-low game", NAME + "'s losing high-low game"]:
                self.load_message_data = True
                self.command_name = "hl"
            elif message.embeds[0].author.name == NAME + "'s meme posting session":
                self.load_message_data = True
                self.command_name = "postmemes"
        except:
            pass

        for command in COMMANDS.keys():
            self.check_message_reference(message_ids[command], command)
    
    def check_message_reference(self, array, command=None):
        try:
            if str(self.message.reference.message_id) in [str(i) for i in array]:
                self.load_message_data = True
                if not command is None:
                    self.command_name = command
                self.loaded_data_dict = self.get_message_data()
                self.dumped_data = json.dumps(self.loaded_data_dict)
        except:
            return False
    
    def press_random_button(self, button_count):
        if not "components" in self.loaded_data_dict: return
        custom_id = self.loaded_data_dict["components"][0]["components"][random.randint(0, button_count - 1)]["custom_id"]
        return self.press_button(custom_id)
    
    def press_button_at_index(self, index):
        custom_id = self.loaded_data_dict["components"][0]["components"][index]["custom_id"]
        return self.press_button(custom_id)
    
    def get_message_data(self):
        url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages/{self.message_id}"
        return requests.get(url, headers={"Authorization": f"Bot {BOT_TOKEN}"}).json()
    
    def press_button(self, custom_id):
        if custom_id == None: return 204
        payload = {
            "type": 3,
            "nonce": str((int(time.time())*1000-1420070400000)*4194304),
            "session_id": "".join(random.choices(string.ascii_letters + string.digits, k=16)),
            "guild_id": GUILD_ID,
            "channel_id": CHANNEL_ID,
            "message_flags": 0,
            "message_id": str(self.message_id),
            "application_id": DANK_MEMER_ID,
            "data": {
                "component_type": 2,
                "custom_id": custom_id
            }
        }
        return requests.post(f"https://discord.com/api/v9/interactions", headers={"Authorization": USER_TOKEN}, json=payload).status_code
    
    def highlow_get_hint_number(self):
        return int(self.loaded_data_dict["embeds"][0]["description"].split("**")[1])
    
    def trivia_get_question(self):
        return self.loaded_data_dict["embeds"][0]["description"].split("**")[1].split("**")[0]
    
    def trivia_get_category(self):
        return self.loaded_data_dict["embeds"][0]["fields"][1]["value"].replace("`", "")
    
    def add_and_log(self, command_name, value):
        if not command_name in earnings:
            earnings[command_name] = 0
        earnings[command_name] += value
        log(f"{command_name.ljust(9)} -> {str(value).ljust(6)} ({sum(earnings.values()) - sum(costs.values())})", LogType.EARN)
    
    def remove_cost(self, command_name, cost):
        if not command_name in costs:
            costs[command_name] = 0
        costs[command_name] += cost

message_ids = {item: [] for item in COMMANDS.keys()}
robbery_target_message_ids = []
padlock_use_msg_ids = []
use_counts = {}
next_use = {}
earnings = {}
costs = {}
running = True
buy_lifesavers = True

# Full command list template, with crime enabled
# active_commands = ["hl", "beg", "search", "postmemes", "dig", "fish", "hunt", "sell", "crime", "trivia", "dep max", "work"]
active_commands = ["hl", "beg", "search", "postmemes", "dig", "fish", "hunt", "sell", "trivia", "dep max", "work"]

client = discord.Client()

@tasks.loop(seconds=2.5)
async def command_start_loop():
    if not running: return
    for command, cooldown in COMMANDS.items():
        if not command in active_commands:
            continue
        if not command in use_counts.keys():
            use_counts[command] = 0
        if not command in next_use.keys():
            next_use[command] = time.time() + random.randint(0, 15)
        if time.time() > next_use[command]:
            next_use[command] = time.time() + cooldown + 3
            use_counts[command] += 1
            res = post_message(f"pls {command}")
            if not res == False:
                message_ids[command].append(res)
            return

@client.event
async def on_ready():
    log(f"Logged in as {client.user.display_name}#{client.user.discriminator} ({client.user.id})", LogType.INFO)
    log(f"Listening for commands on Channel ID {CHANNEL_ID}" , LogType.INFO)
    padlock_use_msg_ids.append(post_message("pls use padlock"))
    await asyncio.sleep(3)
    command_start_loop.start()

@client.event
async def on_message(message: discord.Message):
    global running, buy_lifesavers, CHANNEL_ID, GUILD_ID
    if str(message.author.id) in AUTHORIZED_USERS:
        if message.content.split(" ")[0] == "dmbot":
            args = message.content.split(" ")[1:]

            async def show_help():
                embed = discord.Embed(title="Dank Memer Bot - Help", description="List of available commands for Dank Memer Bot:", color=0x00ff00)
                embed.add_field(name="**`dmbot help`**", value="Shows this help message", inline=False)
                embed.add_field(name="**`dmbot stop`**", value="Pauses excecution of new commands.", inline=False)
                embed.add_field(name="**`dmbot restart`**", value="Restarts excecution of new commands.", inline=False)
                embed.add_field(name="**`dmbot shutdown`**", value="Shut down the bot and exit the script.", inline=False)
                embed.add_field(name="**`dmbot status`**", value="Shows the current status of the bot.", inline=False)
                embed.add_field(name="**`dmbot lifesavers <on|off>`**", value="Choose if a new lifesaver should be purchased when you die.", inline=False)
                embed.add_field(name="**`dmbot active`**", value="List all active commands which are in the event loop.", inline=False)
                embed.add_field(name="**`dmbot enable <command>`**", value="Stop running a command if it is not already running.", inline=False)
                embed.add_field(name="**`dmbot disable <command>`**", value="Start running a command if it is not running.", inline=False)
                embed.add_field(name="**`dmbot transfer <channelid>`**", value="Move the bot to the specified channel.", inline=False)
                embed.add_field(name="**`dmbot detach`**", value="Wherever the bot is running, move it into the current channel.", inline=False)
                embed.add_field(name="**`dmbot summary`**", value="Show current statistics on costs and profits.", inline=False)
                embed.set_footer(text="Created by Mystical")
                await message.channel.send(embed=embed)

            if len(args) == 0:
                await show_help()

            if len(args) > 0:
                if args[0] in ["help", "h"]:
                    await show_help()

                if args[0] in ["stop", "pause", "s"]:
                    await message.reply("Bot is already stopped..." if not running else "Stopping bot...")
                    running = False

                elif args[0] in ["restart", "start", "r", "resume"]:
                    await message.reply("Bot is already running..." if running else "Restarting bot...")
                    running = True

                elif args[0] in ["shutdown", "sd"]:
                    await message.reply("Shutting down...")
                    client.loop.stop()

                elif args[0] in ["transfer", "move"]:
                    if len(args) > 1:
                        CHANNEL_ID = args[1]
                        GUILD_ID = get_guild_id(CHANNEL_ID)
                        try:
                            await message.reply(f"Detaching from this channel, moving to `{CHANNEL_ID}`.")
                        except:
                            pass
                    else:
                        await message.reply(f"Usage: `dmbot {args[0]} <channel>`")

                elif args[0] in ["detach", "d", "pull"]:
                    if not message.guild == None:
                        GUILD_ID = message.guild.id
                        chan = client.get_channel(int(CHANNEL_ID))
                        await chan.send(f"Detaching from this channel. Goodbye!")
                        CHANNEL_ID = message.channel.id
                        await message.reply("Forcefully moving operations to this channel.")
                    else:
                        await message.reply("Unable to move operations to this channel.")

                elif args[0] in ["lifesavers", "ls"]:
                    if len(args) > 1:
                        if args[1] in ["on", "enabled", "enable", "yes"]:   
                            buy_lifesavers = True
                            await message.reply("Lifesavers will now be bought.")
                        elif args[1] in ["off", "disabled", "disable", "no"]:
                            buy_lifesavers = False
                            await message.reply("Lifesavers will no longer be bought.")
                        else:
                            await message.reply("Invalid input.")
                    else:
                        await message.reply("Please specify whether you want to buy lifesavers.")

                elif args[0] == "enable":
                    if len(args) > 1:
                        if args[1] in COMMANDS.keys():
                            if not args[1] in active_commands:
                                active_commands.append(args[1])
                                await message.reply(f"Enabled `{args[1]}`")
                            else:
                                await message.reply(f"`{args[1]}` is already enabled.")
                        else:
                            await message.reply(f"`{args[1]}` is not a valid command.")
                    else:
                        await message.reply("Please specify a command to enable.")

                elif args[0] == "disable":
                    if len(args) > 1:
                        if args[1] in COMMANDS.keys():
                            if args[1] in active_commands:
                                active_commands.remove(args[1])
                                await message.reply(f"Disabled `{args[1]}`.")
                            else:
                                await message.reply(f"`{args[1]}` is already disabled.")
                        else:
                            await message.reply(f"`{args[1]}` is not a valid command.")
                    else:
                        await message.reply("Please specify a command to disable.")

                elif args[0] == "active":
                    mods = "`, `".join(active_commands)
                    await message.reply(f"Active commands: {f'`{mods}`' if not mods == '' else 'None'}")

                elif args[0] == "status":
                    mods = "`, `".join(active_commands)
                    embed = discord.Embed(title="Dank Memer Bot - Status", description="Current bot information:", color=0x00ff00)
                    embed.add_field(name="**Active Commands:**", value=f"`{mods}`" if not mods == "" else "None", inline=False)
                    embed.add_field(name="**Total Known Commands:**", value=f"`{len(COMMANDS)}`", inline=False)
                    embed.add_field(name="**Total Commands Sent:**", value=f"`{sum(use_counts.values())}`", inline=False)
                    bd_description = f"➤ {', '.join(f'{key}: `{value}`' for key, value in use_counts.items())}"
                    embed.add_field(name="**Breakdown:**", value=bd_description, inline=False)
                    embed.add_field(name="**Session Costs:**", value=f"`{sum(costs.values())}`", inline=False)
                    embed.add_field(name="**Session Intake:**", value=f"`{sum(earnings.values())}`", inline=False)
                    embed.add_field(name="**Session Profit:**", value=f"`{sum(earnings.values()) - sum(costs.values())}`", inline=False)
                    embed.set_footer(text="Created by Mystical")
                    await message.channel.send(embed=embed)
            
                elif args[0] == "summary":
                    embed = discord.Embed(title="Dank Memer Bot - Summary", description="Current bot information:", color=0x00ff00)
                    embed.add_field(name="**Total Intake**", value=f"`{sum(earnings.values())}`", inline=True)
                    embed.add_field(name="**Total Costs**", value=f"`{sum(costs.values())}`", inline=True)
                    embed.add_field(name="**Net Profit**", value=f"`{sum(earnings.values()) - sum(costs.values())}`", inline=True)
                    if len(earnings) > 0:
                        earning_bd = "\n".join(f"{key}: `{value}`" for key, value in earnings.items())
                        embed.add_field(name="**Earning Breakdown**", value=earning_bd, inline=False)
                    if len(costs) > 0:
                        costs_bd = "\n".join(f"{key}: `{value}`" for key, value in costs.items())
                        embed.add_field(name="**Cost Breakdown**", value=costs_bd, inline=False)
                    embed.set_footer(text="Created by Mystical")
                    await message.channel.send(embed=embed)

                else:
                    await show_help()

    for item in STEAL_FLAGS:
        if item in message.content.lower():
            try:
                log(f"{message.author.display_name} attempted to rob you.", LogType.ROBBERY)
                robbery_target_message_ids.append(message.id)
            except:
                pass

    if not message.author.id == DANK_MEMER_ID: return
    bot_message = BotMessage(message)

    if "a massive padlock on their wallet" in message.content:
        bot_message.check_message_reference(robbery_target_message_ids)
        if not bot_message.loaded_data_dict is None:
            running = False
            await asyncio.sleep(10)
            try:
                padlock_use_msg_ids.append(post_message("pls use padlock"))
                await asyncio.sleep(5)
            except:
                pass
            running = True
    
    elif "You don't own this item" in message.content:
        bot_message.check_message_reference(padlock_use_msg_ids)
        if not bot_message.loaded_data_dict is None:
            running = False
            await asyncio.sleep(10)
            try:
                post_message("pls with 15000")
                await asyncio.sleep(5)
                post_message("pls buy padlock 3")
                log("Purchased a padlock.", LogType.ROBBERY)
                await asyncio.sleep(5)
                padlock_use_msg_ids.append(post_message("pls use padlock"))
            except:
                pass
            running = True
        
    elif "Your wallet now has a padlock on it." in message.content:
        bot_message.check_message_reference(padlock_use_msg_ids)
        if not bot_message.loaded_data_dict is None:
            running = False
            await asyncio.sleep(10)
            try:
                padlock_quantity_remaining = int(message.content.split("You have ")[1].split("x Padlock")[0])
                if padlock_quantity_remaining < 3:
                    post_message(f"pls with {(3 - padlock_quantity_remaining) * 5000}")
                    await asyncio.sleep(5)
                    post_message(f"pls buy padlock {3 - padlock_quantity_remaining}")
                    log("Purchased a padlock.", LogType.ROBBERY)
                    await asyncio.sleep(5)
            except:
                pass
            running = True
    
    try:

        if "event" in message.content:
            if "Attack the boss by clicking" in message.content:
                while True:
                    status_code = bot_message.press_button_at_index(0)
                    bot_message.press_button_at_index(0)
                    await asyncio.sleep(0.5)
                    if not status_code == 204:
                        break
            
            elif "Trivia" in message.content:
                question = bot_message.trivia_get_question()
                category = bot_message.trivia_get_category()
                target_id = get_correct_trivia_id(bot_message.loaded_data_dict, question, category)
                await asyncio.sleep(random.randint(2, 5))
                if target_id is None:
                    bot_message.press_random_button(4)
                else:
                    bot_message.press_button(target_id)

            elif "secret number" in message.content:
                if bot_message.highlow_get_hint_number() <= 50:
                    bot_message.press_button_at_index(2)
                else:
                    bot_message.press_button_at_index(0)

            elif "Results for" in message.content:
                value = int(bot_message.dumped_data.split("⏣")[1].split("and")[0])
                bot_message.add_and_log("Event", value)

        if bot_message.command_name == "hl":
            if bot_message.highlow_get_hint_number() <= 50:
                bot_message.press_button_at_index(2)
            else:
                bot_message.press_button_at_index(0)

        elif bot_message.command_name == "search":
            bot_message.press_button(get_ideal_search_id(bot_message.loaded_data_dict))

        elif bot_message.command_name == "postmemes":
            bot_message.press_random_button(5)

        elif bot_message.command_name == "trivia":
            question = bot_message.trivia_get_question()
            category = bot_message.trivia_get_category()
            target_id = get_correct_trivia_id(bot_message.loaded_data_dict, question, category)
            await asyncio.sleep(random.randint(2, 5))
            if target_id is None:
                bot_message.press_random_button(4)
            else:
                bot_message.press_button(target_id)
        
        elif bot_message.command_name == "sell":
            if "Multi Bonus" in bot_message.dumped_data:
                value = int(bot_message.dumped_data.split("\\u23e3 ")[1].split("`")[0].replace(",", ""))
                bot_message.add_and_log("Sell", value)
            elif not "no sellable" in message.content:
                bot_message.press_button_at_index(1)

        elif bot_message.command_name == "crime":
            bot_message.press_random_button(3)
    
        elif bot_message.command_name == "beg":
            if "Multi Bonus" in bot_message.dumped_data:
                value = int(bot_message.dumped_data.split("\\u23e3 ")[1].split("**")[0].replace(",", ""))
                bot_message.add_and_log("Beg", value)
        
        elif bot_message.command_name == "fish":
            if "You don't have a fishing pole" in message.content:
                log(f"BOUGHT FISHING ROD WHILE FISHING #{use_counts['fish']}", LogType.BUY)
                post_message("pls buy fishingpole")
                bot_message.remove_cost("Fish", 25000)
            elif "Catch the fish!" in message.content:
                target = message.content.split("\n")[1]
                emoji = ":legendaryfish:" if "Legendary" in target else ":Kraken:"
                if target.split(emoji)[0] == "       ":
                    bot_message.press_button_at_index(1)
                elif target.split(emoji)[0] == "":
                    bot_message.press_button_at_index(0)
                else:
                    bot_message.press_button_at_index(2)
            elif "Bank Note" in message.content:
                post_message("pls use banknote 1")
        
        elif bot_message.command_name == "dig":
            if "You don't have a shovel" in message.content:
                log(f"BOUGHT SHOVEL WHILE DIGGING #{use_counts['dig']}", LogType.BUY)
                post_message("pls buy shovel")
                bot_message.remove_cost("Dig", 25000)
        
        elif bot_message.command_name == "hunt":
            if "the dragon ate you" in message.content:
                log(f"DIED HUNTING #{use_counts['hunt']}", LogType.DIED)
                if not buy_lifesavers:
                    log(f"SKIPPED LIFESAVER PURCHASE", LogType.BUY)
                else:
                    log(f"PURCHASED LIFESAVER", LogType.BUY)
                    post_message("pls buy livesaver")
                    bot_message.remove_cost("Hunt", 50000)
            elif "Dodge the Fireball" in message.content:
                target = message.content.split("\n")[2]
                if target.split(":FireBall:")[0] == "":
                    bot_message.press_button_at_index(2)
                else:
                    bot_message.press_button_at_index(0)
            elif "Bank Note" in message.content:
                post_message("pls use banknote 1")
        
        elif bot_message.command_name == "work":
            if "Your salary has increased" in message.content:
                post_message('pls work')
            
            elif "You don't currently have a job to work at" in message.content:
                post_message('pls work babysitter')
                await asyncio.sleep(5)
                post_message('pls work')
            
            elif "Hit the Ball!" in message.content:

                # TODO Dubious, must test

                if message.content.split(":soccer:")[0] == "":
                    bot_message.press_button_at_index(2)
                else:
                    bot_message.press_button_at_index(0)
            
            elif "Dunk the ball!" in message.content:

                # TODO Also dubious

                if message.content.split(":basketball:")[0] == "       ":
                    bot_message.press_button_at_index(1)
                elif message.content.split(":basketball:")[0] == "":
                    bot_message.press_button_at_index(0)
                else:
                    bot_message.press_button_at_index(2)
            
            elif "Repeat Order" in message.content:

                # TODO Dubious

                work_list = [bot_message.dumped_data.split("Remember words order! ")[1].replace("", ", ")]
                labels, label_list = get_label_mapping_and_list(bot_message)
                await asyncio.sleep(6)
                for item in work_list:
                    if item in label_list:
                        bot_message.press_button_at_index(label_list.index(item))
            
            elif "color" in message.content:

                # TODO Mmmm how to select color with only one dumped data split?

                work_copy = [bot_message.dumped_data.split("selected word. ")[1]]
                labels, label_list = get_label_mapping_and_list(bot_message)
                await asyncio.sleep(6)
                for item in work_copy:
                    if item in label_list:
                        bot_message.press_button_at_index(label_list.index(item))
            
            elif "emoji closely!" in message.content:

                # TODO Dubious at best

                work_copy = [bot_message.dumped_data.split("Look at the emoji closely! ")[1]]
                labels, label_list = get_label_mapping_and_list(bot_message)
                await asyncio.sleep(6)
                for item in work_copy:
                    if item in label_list:
                        bot_message.press_button_at_index(label_list.index(item))
    except:
        pass

@client.event
async def on_message_edit(_, message: discord.Message):
    if not message.author.id == DANK_MEMER_ID: return

    try:
        bot_message = BotMessage(message)

        if bot_message.command_name == "hl":
            if not "You lost!" in bot_message.dumped_data:
                value = int(bot_message.dumped_data.split("**!")[0].split(" ")[-1].replace(",", ""))
                bot_message.add_and_log("High/Low", value)

        elif bot_message.command_name == "postmemes":
            if "earned" in bot_message.dumped_data:
                value = int(bot_message.dumped_data.split("**\\u23e3 ")[1].split("**")[0].replace(",", ""))
                if value > 0:
                    bot_message.add_and_log("Postmemes", value)
            if "Bank Note" in bot_message.dumped_data:
                post_message("pls use banknote 1")
        
        elif bot_message.command_name == "crime":
            for message_chunk in CRIME_DEATH_CHUNKS:
                if message_chunk in bot_message.loaded_data_dict:
                    log(f"DIED COMMITTING CRIME #{use_counts['crime']}", LogType.DIED)
                    if not buy_lifesavers:
                        log(f"SKIPPED LIFESAVER PURCHASE", LogType.BUY)
                    else:
                        log(f"PURCHASED LIFESAVER", LogType.BUY)
                        post_message("pls buy livesaver")
                        bot_message.remove_cost("Crime", 50000)
                    break
            if f"{NAME} committed" in bot_message.dumped_data and "\\u23e3" in bot_message.dumped_data:
                buffer = ""
                for char in bot_message.dumped_data.split("\\u23e3 ")[1]:
                    if char in "0123456789,":
                        buffer += char 
                    else:
                        break
                value = int(buffer.replace(",", ""))
                bot_message.add_and_log("Crime", value)
            if "Bank Note" in bot_message.dumped_data:
                post_message("pls use banknote 1")
        
        elif bot_message.command_name == "search":
            if not "Guess you didn't" in message.content:
                if "description" in bot_message.loaded_data_dict["embeds"][0]:
                    for message_chunk in SEARCH_DEATH_CHUNKS:
                        if message_chunk in bot_message.loaded_data_dict["embeds"][0]["description"]:
                            log(f"DIED DOING SEARCH #{use_counts['search']}", LogType.DIED)
                            if not buy_lifesavers:
                                log(f"SKIPPED LIFESAVER PURCHASE", LogType.BUY)
                            else:
                                log(f"PURCHASED LIFESAVER", LogType.BUY)
                                post_message("pls buy livesaver")
                                bot_message.remove_cost("Search", 50000)
                            break
                if f"{NAME} searched" in bot_message.dumped_data and "\\u23e3" in bot_message.dumped_data:
                    buffer = ""
                    for char in bot_message.dumped_data.split("\\u23e3 ")[1]:
                        if char in "0123456789,":
                            buffer += char
                        else:
                            break
                    value = int(buffer.replace(",", ""))
                    bot_message.add_and_log("Search", value)
        
        elif bot_message.command_name == "trivia":
            if "You got that answer correct" in bot_message.dumped_data:
                value = int(bot_message.dumped_data.split("you also got ")[1].split(" coins")[0].replace(",", ""))
                bot_message.add_and_log("Trivia", value)
        
        elif bot_message.command_name == "work":
            if "You were given" in bot_message.dumped_data:
                value = int(bot_message.dumped_data.split("You were given ")[1].split(" for")[0].replace(",", ""))
                bot_message.add_and_log("Work", value)
    except:
        pass

client.run(BOT_TOKEN)
print("\033[0m\r", end="")
log(f"Total Income:   ⏣ {sum(earnings.values())}", LogType.SUMMARY)
log(f"Total Expenses: ⏣ {sum(costs.values())}", LogType.SUMMARY)
log(f"Total Profit:   ⏣ {sum(earnings.values()) - sum(costs.values())}", LogType.SUMMARY)
if len(earnings) > 0:
    log(f"Earning Breakdown:", LogType.SUMMARY)
for key, value in earnings.items():
    log(f" > {key}: ⏣ {value}", LogType.SUMMARY)
if len(costs) > 0:
    log(f"Cost Breakdown:", LogType.SUMMARY)
for key, value in costs.items():
    log(f" > {key}: ⏣ {value}", LogType.SUMMARY)
