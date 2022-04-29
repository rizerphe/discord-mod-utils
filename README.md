# Discord mod utils
A simple set of moderation utilities written with pycord

Backstory: in a server I moderate, we create a thread in our #mod-cases channel every time a user does something and we need to discuss it. However doing that takes way too much time, plus we then usually run the same set of commands to get the server join date etc in that thread, and we usually delete the original user's message (the one that started the case). This also means that we usually post a screenshot of that message to the moderation thread so that other mods can later understand what happened. This bot allows us to create such a thread by just right-clicking any message in the server, and it also shows all of the message and user info we need in the thread while also copying the message over into the thread using a webhook.

# Running
## Installing using pip
You should probably do this within a virtual environment - this bot uses an unstable beta version of pycord so it might break other stuff you're running.
```sh
pip install git+https://github.com/rizerphe/discord-mod-utils
discord-mod-utils-bot --help
```
## Installing using [pipx](https://github.com/pypa/pipx) (recommended)
This will automatically put everything into a virtual environment so you don't have to worry about it breaking everything
```sh
pipx install git+https://github.com/rizerphe/discord-mod-utils
discord-mod-utils-bot --help
```
## Running
I use firestore for storing per-guild configuration so you'll need to create a new firebase project.
Put your firestore credentials (get them [here](https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk)) into `credentials.json` in the current working directory.
Get your discord bot token. [Here's how to get one](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token)
```sh
discord-mod-utils-bot -t [your token here]
```
## Storing the configuration
I use python-dotenv to allow you to store the token in a `.env` file instead of passing it from the command line every time. Just put `TOKEN = [your token here]` into `.env` in the current working directory
# Development
If you're modifying the code, you probably want to install it in editable mode and configure debug guilds:
```sh
virtuelenv venv
. venv/bin/activate
pip install -e .
discord-mod-utils-bot -t [your token here] -d 000000000000000000 -d 000000000000000000
```
Or configure the debug guilds in the `.env` file:
```env
TOKEN = [your token here]
DEBUG_GUILDS = '[000000000000000000, 000000000000000000]'
```