# AutoDankMemer
Automated bot to farm money on the Dank Memer Discord bot.

Runs a discord.py session on a bot account and sends messages using a user account. The bot has a command system that can only be used by the targeted user account. The commands are listed below.

PLEASE NOTE: While it may seem too easy to farm commands in Dank Memer, the bot does absolutely have an automatic blacklist system which detects spam. It is recommended for you to only use this bot periodically. Leaving running for more than six hours is HIGHLY discouraged and done completely at your own risk.

Fork adds 'pls work', but it is not fully complete/tested yet. If you use it, feedback is highly appreciated.

## Features

### Commands

- Plays `highlow` correctly.
- Begs for coins.
- Only selects places for `search` that never cause death.
- Posts memes.
- Uses `dig` with automatic shovel purchasing.
- Uses `fish` and detects and plays the legendary fish minigame.
- Uses `hunt` and detects and plays the dragon minigame.
- Automatically sells sellable items.
- Automatically purchases lifesavers when you die.
- Plays `trivia` and gets the correct answer for 99% of questions.
- Automatically deposits into the bank.
- Detects if you are robbed and uses a padlock.
- Buys more padlocks if you go under 3 remaining.
- Uses Bank Notes if you find them while fishing, hunting, or posting memes.
- (EXPERIMENTAL) Uses 'work' and correctly plays minigames, and obtains a job if you don't have one.

### Backend

- Logs profits and costs using a fairly advanced parsing system.
- Bot command system for management and statistics.
- Live event queue system which spreads commands out by 2.5 seconds and always keeps the money coming.
- Although there is no documentation, it is decently modular and allows for adding commands easily.
- Supports pressing buttons and using discord interactions.
- Easily move the current operational channel to other servers or channels.

### Notes

- The bot has the capability to use `crime` but it is disabled in the source code because it causes so many deaths and the lifesavers get extremely expensive. Modify the variable `active_commands` at its definition to re-enable it.
- The `trivia` command knows almost all of the questions used by API which Dank Memer uses. However, there are 30-40 questions missing out of roughly 4,000.

## Commands

**`dmbot help`**: Shows this help message.

**`dmbot stop`**: Pauses excecution of new commands.

**`dmbot restart`**: Restarts excecution of new commands.

**`dmbot shutdown`**: Shut down the bot and exit the script.

**`dmbot status`**: Shows the current status of the bot.

**`dmbot lifesavers <on|off>`**: Choose if a new lifesaver should be purchased when you die.

**`dmbot active`**: List all active commands which are in the event loop.

**`dmbot enable <command>`**: Stop running a command if it is not already running.

**`dmbot disable <command>`**: Start running a command if it is not running.

**`dmbot transfer <channelid>`**: Move the bot to the specified channel.

**`dmbot detach`**: Wherever the bot is running, move it into the current channel.

**`dmbot summary`**: Show current statistics on costs and profits.

## Configuration

- Open `AutoDankMemer.py` and go to the python list on line `209`. Edit it and remove any modules you don't want to use.
- Keep the list on line #208 intact and use it as a template. `"crime"` is disabled on line `209` by default.
- Open `BotConfig.json`.
- Have a bot in a server with yourself and Dank Memer.
- Place the bot's token in the space which reads `BOT_TOKEN`.
- Place your own user token in the space which reads `USER_TOKEN`.
- Enable discord developer mode if it is not already on.
- Copy the Channel ID where you want to start out and put it, as a string, in `CHANNEL_ID`. (This can be changed once the bot is running, see the list of commands for more details)
- Optionally, include the `trivia.json` in the same folder as the script is running to let it always get trivia questions correct.
