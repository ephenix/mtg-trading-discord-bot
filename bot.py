import os
import re
import json
import discord
from time import time
from dotenv import load_dotenv

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"An error occurred: {event}")
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

class TradeDialog(discord.ui.Modal):
    def __init__(self, ctx, options, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.options = options
        self.add_item(discord.ui.InputText(label="Want", style=discord.InputTextStyle.long, required=False))
        self.add_item(discord.ui.InputText(label="Have", style=discord.InputTextStyle.long, required=False))

    async def callback(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title=f"{self.ctx.author.global_name}'s Trade Listing")
            embed.add_field(name=f"*WANT*", value=self.children[0].value)
            embed.add_field(name=f"*HAVE*", value=self.children[1].value)
            embed.add_field(name="options",value="\n".join([f"{k}: {v}" for k,v in self.options.items()]))
            data = {
                "want": self.children[0].value,
                "have": self.children[1].value
            }
            await interaction.response.send_message(embeds=[embed])

            if validate(self.children[0].value):
                if validate(self.children[1].value):
                    process(self.ctx.author.id, data, self.options)
                    await find_matches(self.ctx)
                else:
                    await self.ctx.respond("Input validation error with 'Have' field. Please use moxfield format ie:\n1 Ajani, Nacatl Pariah // Ajani, Nacatl Avenger (MH3) 237\n1 Atraxa, Grand Unifier (ONE) 316\n5 Blood Crypt (RTR) 238", ephemeral=True)
            else:
                await self.ctx.respond("Input validation with 'Want' field. Please use moxfield format ie:\n1 Ajani, Nacatl Pariah // Ajani, Nacatl Avenger (MH3) 237\n1 Atraxa, Grand Unifier (ONE) 316\n5 Blood Crypt (RTR) 238", ephemeral=True)
        except Exception as e:
            await self.ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)

def validate(text):
    validator = r"^(\d{1,}) (.+?) (\(.+)$"
    if text:
        for line in text.split("\n"):
            if line:
                if not re.match(validator, line):
                    return False
    return True

@bot.slash_command()
async def trade(ctx: discord.ApplicationContext,
                mode: discord.Option(str, 
                                     choices=['add','overwrite'],
                                     default="overwrite", 
                                     description="Overwrite existing orders or add new?"
                                    ), # type: ignore
                strict_version: discord.Option(bool,description="Look only for the specified version.",default=False), # type: ignore
                trade_only: discord.Option(bool,description="Search only for cards for trade",default=False), # type: ignore
                sell_only: discord.Option(bool,description="List cards as only for sale, not trades",default=False), # type: ignore
            ):
    try:
        print(f"trade function called by {ctx.author.global_name}({ctx.author.id})")
        options = {
            'mode': mode,
            'strict_version': strict_version,
            'trade_only': trade_only,
            'sell_only': sell_only
        }
        modal = TradeDialog(ctx, options, title="Trade Dialog")
        await ctx.send_modal(modal)
    except Exception as e:
        await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)

@bot.slash_command()
async def trade_help(ctx: discord.ApplicationContext):
    try:
        print(f"help function called by {ctx.author.global_name}({ctx.author.id})")
        await ctx.respond("""
# Using the `/trade` command.

Parameters: 
                          
* `mode` (add | **overwrite**): Overwrite is the default -- each time you run the trade command, all of your orders are replaced by the new list.

* `strict_version` (True | **False**) -- metadata applied to "Want" cards -- if True, these cards will only match 'haves' if the set/version matches.

* `trade_only` (True | **False**) -- metadata applied to "Want" cards -- if True, will only match 'haves' that do NOT have the 'sell_only" flag applied.

* `sell_only` (True | **False**) -- metadata applied to "Have" cards -- if True, will only match 'wants' that do NOT have "trade_only" flag applied.

The bot will then present a modal dialog with two fields:

* `want` - text box which takes a list of cards exported from moxfield.

* `have` - text box which takes a list of cards exported from moxfield.
                          
---
                          
# Examples:

`/trade strict_version=True
    wanted:
        1 Black Lotus (LEA) 232
    have:
        1 Vizzerdrix (7ED) 110
                          
---

`/list_trades @<username>`
                          
---
                          
`/find_matches`
                          
---
                          
""", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)

@bot.slash_command()
async def list_trades(ctx: discord.ApplicationContext,
                      user: discord.User):
    try:
        print(f"list_trades function called by {ctx.author.global_name}({ctx.author.id})")
        if f"{user.id}" in database['users']:
            
            has = []
            for card in database['users'][f"{user.id}"]['have']:
                s = f"{card['quantity']}x {card['card']} {card['version']}"
                if card['sell_only']:
                    s += " (FOR SALE ONLY)"
                has.append(s)
            await ctx.respond(f"<@{user.id}> HAS: \n" + "\n".join(has), ephemeral=True)
            wants = []
            for card in database['users'][f"{user.id}"]['want']:
                s = f"{card['quantity']}x {card['card']} {card['version']}"
                if card['strict_version']:
                    s += " (EXACT MATCH)"
                wants.append(s)

            await ctx.respond(f"<@{user.id}> WANTS: \n" + "\n".join(wants), ephemeral=True)
        else:
            await ctx.respond(f"no trades found for user <@{user.id}>.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)


@bot.slash_command()
async def find_matches(ctx: discord.ApplicationContext):
    try:
        print(f"find_matches function called by {ctx.author.global_name}({ctx.author.id})")
        for card in database['users'][f"{ctx.author.id}"]["want"]:
            if card['card'] in database['cards']["have"]:
                for entry_id, entry_data in database['cards']['have'][card['card']].items():
                    if entry_data["userid"] != card["userid"]:
                        if(card['trade_only']==False or entry_data["sell_only"] == False):
                            if(card['strict_version']==True):
                                if(card['version'] == entry_data['version']):
                                    await ctx.respond(f"<@{entry_data['userid']}> has a {entry_data['card']} {entry_data['version']} available!",ephemeral=True)
                            else:
                                await ctx.respond(f"<@{entry_data['userid']}> has a {card['card']} available!",ephemeral=True)
        for card in database['users'][f"{ctx.author.id}"]["have"]:
            if card['card'] in database['cards']["want"]:
                for entry_id, entry_data in database['cards']['want'][card['card']].items():
                    if entry_data["userid"] != card["userid"]:
                        if(entry_data['trade_only']==False or card["sell_only"] == False):
                            if(entry_data['strict_version']==True):
                                if(entry_data['version'] == card['version']):
                                    await ctx.respond(f"<@{entry_data['userid']}> may be interested in your {card['card']} {card['version']}!", ephemeral=True)
                            else:
                                await ctx.respond(f"<@{entry_data['userid']}> may be interested in your {card['card']}!", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"An error occurred: {str(e)}", ephemeral=True)

def process(userid, data, options):
    try:
        t = time()
        if f"{userid}" not in database['users']:
            database['users'][f"{userid}"] = {
                "have": [],
                "want": []
            }
        for method in ["have", "want"]:
            if options["mode"] == "overwrite":
                for card in database['users'][f"{userid}"][method]:
                    #remove the entry from the cards database
                    if card['uid'] in database['cards'][method][card['card']]:
                        database['cards'][method][card['card']].pop(card['uid'])
                # clear the user's requests for this method
                database['users'][f"{userid}"][method] = []
            for line in data[method].split("\n"):
                if line:
                    linedata = re.match(r"(\d{1,}) (.+?) (\(.+)",line)
                    quantity = linedata.group(1)
                    card = linedata.group(2)
                    version = linedata.group(3)
                    uid = f"{userid}-{version}-{t}"
                    entry = {
                            'userid': f"{userid}",
                            'quantity':quantity,
                            'card':card, 
                            'version':version, 
                            'last_updated': t, 
                            'uid':uid
                    }
                    if method=="want":
                        entry["strict_version"] = options["strict_version"]
                        entry["trade_only"] = options["trade_only"]
                    if method=="have":
                        entry["sell_only"] = options["sell_only"]
                    database['users'][f"{userid}"][method].append(entry)
                    # add the card request to the cards index.
                    if card not in database['cards'][method]:
                        database['cards'][method][card] = {}
                    database['cards'][method][card][uid] = entry
        write_database()
    except Exception as e:
        print(f"An error occurred while processing data: {str(e)}")

# --------------------------

base_dir = os.path.dirname(__file__)
database_path = f"{base_dir}/database.json"
database={}

def load_database():
    global database
    try:
        if not os.path.exists(database_path):
            database = {"users":{},"cards":{"want":{},"have":{}}}
            write_database()
        else:
            with open(database_path, "r") as db:
                database = json.load(db)
        print("database loaded.")
    except Exception as e:
        print(f"An error occurred while loading the database: {str(e)}")

def write_database():
    try:
        with open(database_path, "w") as db:
            json.dump(database,db,indent=4)
        print("writing database")
    except Exception as e:
        print(f"An error occurred while writing the database: {str(e)}")

load_dotenv()

load_database()
if(database):
    try:
        bot.run(os.getenv('TOKEN'))
    except Exception as e:
        print(f"An error occurred while running the bot: {str(e)}")
else:
    raise BaseException("Could not load database")