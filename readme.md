# Welcome to the MTG Trading Discord Bot.
- This is a bot which tracks the cards people are hunting for and/or offering to trade!
- Begin by creating a moxfield decklist for your want list and your 'have' list.
- You can create two separate decks, or use the sideboard function to keep these lists separate.
- Remember to add the correct set and version of cards to the deck if you are offering -- this tool supports strict version matching.
- Once complete, export your decklist using the "export for moxfield" option, which includes the set / version data for each card.

Using the `/trade` command.

`/trade` has 4 optional parameters:

* `mode` (add | **overwrite**): Overwrite is the default -- each time you run the trade command, all of your orders are replaced by the new list.

    If you have some orders you wish to have unique settings for -- such as some cards you care about the set/version, and other you don't,
    add these separately using the "add" mode.

* `version_strict_search` (True | **False**) -- metadata applied to "Want" cards -- if True, these cards will only match 'haves' if the set/version matches.

* `trade_only` (True | **False**) -- metadata applied to "Want" cards -- if True, will only match 'haves' that do NOT have the 'sell_only" flag applied.

* `sell_only` (True | **False**) -- metadata applied to "Have" cards -- if True, will only match 'wants' that do NOT have "trade_only" flag applied.

The bot will then present a modal dialog with two fields:

* `want` - text box which takes a list of cards exported from moxfield.

* `have` - text box which takes a list of cards exported from moxfield.


Additionally, there is a 4000 character limit to the have and the want text boxes. To add additional orders, use the 'add' mode on a separate command. This is a discord limitation.

---

# Running the bot

* create a discord app
* create a .env file with your discord app token:

```
TOKEN = <token>
```

* add the app to your server
* run bot.py

* eventually, host this on a server somewhere.

Someday this will be a public bot with per-server storage and optional global trade requests. Today is not that day.