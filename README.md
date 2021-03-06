# CrumblyRedditor
 Discord bot posting stuff from Reddit every 24 hours built with Discord.py and aPRAW

## Requirements
 - [Python](https://www.python.org/) (versions from 3.6 and up will be probably fine)
 - For more see [requirements.txt](requirements.txt)

## Setting up the bot
 1. Install Python
 2. Clone this repository.
 3. Go to the repository destination and run `pip install -r requirements.txt`
 4. Rename `config_example.json` to `config.json` and set important variables.
 ```
{
    "token": "token", <- your discord bot token
    "reddit": {
        "username": "username", <- reddit username
        "password": "password", <- reddit password
        "client_id": "client_id", <- ID of your reddit aplication
        "client_secret": "client_secret", <- secret of your reddit aplication
        "user_agent": "user_agent" <- useragent as specified by Reddit API docs
    },
    "prefix": "r/" <- default prefix
}
```

## Running the bot
 You have two options:
 1) Running the bot directly: `py CrumblyRedditor/bot.py`
 2) Running it through docker: `docker build -t crumblyredditor .` + `docker run -d crumblyredditor`

## Issues
 If you encounter any bugs create an issue and I'll try to resolve the porblem.

## Limitations
 - Only works for guilds.
 - Posts at one predefined time (not ideal for multiple guilds)

These limitations might get resolved later. If you need them now create an issue.

## Contribution
 If you want to improve the bot feel free to make a pull request!

## Lincense
 [GNU GPLv3](LICENSE)
