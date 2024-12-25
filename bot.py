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

class TradeDialog(discord.ui.Modal):
    def __init__(self, ctx, options, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ctx = ctx
        self.options = options
        self.add_item(discord.ui.InputText(label="Want", style=discord.InputTextStyle.long, required=False))
        self.add_item(discord.ui.InputText(label="Have", style=discord.InputTextStyle.long, required=False))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.ctx.author.global_name}'s Trade Listing")
        embed.add_field(name=f"*WANT* (version-strict: {self.options['version_strict_search']}, trade-only: {self.options['trade_only']})", value=self.children[0].value)
        embed.add_field(name=f"*HAVE* (sell_only: {self.options['sell_only']})", value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])
        data = {
            "want": self.children[0].value,
            "have": self.children[1].value
        }

        if validate(self.children[0].value):
            if validate(self.children[1].value):
                process(self.ctx.author.id,data,self.options)
                await find_matches(self.ctx)
            else:
                await self.ctx.respond("Input validation error with 'Have' field. Please use moxfield format ie:\n1 Ajani, Nacatl Pariah // Ajani, Nacatl Avenger (MH3) 237\n1 Atraxa, Grand Unifier (ONE) 316\n5 Blood Crypt (RTR) 238",ephemeral=True)
        else:
            await self.ctx.respond("Input validation with 'Want' field. Please use moxfield format ie:\n1 Ajani, Nacatl Pariah // Ajani, Nacatl Avenger (MH3) 237\n1 Atraxa, Grand Unifier (ONE) 316\n5 Blood Crypt (RTR) 238",ephemeral=True)
            

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
                version_strict_search: discord.Option(bool,description="Look only for the specified version.",default=False), # type: ignore
                trade_only: discord.Option(bool,description="Search only for cards for trade",default=False), # type: ignore
                sell_only: discord.Option(bool,description="List cards as only for sale, not trades",default=False), # type: ignore
            ):
    print(f"trade function called by {ctx.author.global_name}({ctx.author.id})")
    options = {
        'mode': mode,
        'version_strict_search': version_strict_search,
        'trade_only': trade_only,
        'sell_only': sell_only
    }
    modal = TradeDialog(ctx,options,title="Trade Dialog")
    await ctx.send_modal(modal)

@bot.slash_command()
async def trade_help(ctx: discord.ApplicationContext):
    print(f"help function called by {ctx.author.global_name}({ctx.author.id})")
    await ctx.respond("""
# Welcome to the MTG Trading Discord Bot.
- This is a bot which tracks the cards people are hunting for and/or offering to trade!
- Begin by creating a moxfield decklist for your want list and your 'have' list.
- You can create two separate decks, or use the sideboard function to keep these lists separate.
- Remember to add the correct set and version of cards to the deck if you are offering -- this tool supports strict version matching.
- Once complete, export your decklist using the "export for moxfield" option, which includes the set / version data for each card.

Using the `/trade` command.
`/trade` has 4 optional parameters:
    `mode` (add | **overwrite**): Overwrite is the default -- each time you run the trade command, all of your orders are replaced by the new list.
        If you have some orders you wish to have unique settings for -- such as some cards you care about the set/version, and other you don't,
        add these separately using the "add" mode.
    `version_strict_search` (True | **False**) -- metadata applied to "Want" cards -- if True, these cards will only match 'haves' if the set/version matches.
    `trade_only` (True | **False**) -- metadata applied to "Want" cards -- if True, will only match 'haves' that do NOT have the 'sell_only" flag applied.
    `sell_only` (True | **False**) -- metadata applied to "Have" cards -- if True, will only match 'wants' that do NOT have "trade_only" flag applied.
                      
    `want` - text box which takes a list of cards exported from moxfield.
    `have` - text box which takes a list of cards exported from moxfield.

Additionally, there is a 4000 character limit to the have and the want text boxes. To add additional orders, use the 'add' mode on a separate command. This is a discord limitation.
                     
                      """, ephemeral=True)

@bot.slash_command()
async def list_trades(ctx: discord.ApplicationContext,
                      user: discord.User):
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
            if card['version_strict_search']:
                s += " (EXACT MATCH)"
            wants.append(s)

        await ctx.respond(f"<@{user.id}> WANTS: \n" + "\n".join(wants), ephemeral=True)
    else:
        await ctx.respond(f"no trades found for user <@{user.id}>.", ephemeral=True)

# --------------------------

async def find_matches(ctx):
        for card in database['users'][f"{ctx.author.id}"]["want"]:
            if card['card'] in database['cards']["have"]:
                for entry_id, entry_data in database['cards']['have'][card['card']].items():
                    if entry_data["userid"] != card["userid"]:
                        if(card['trade_only']==False or entry_data["sell_only"] == False):
                            if(card['version_strict_search']==True):
                                if(card['version'] == entry_data['version']):
                                    await ctx.respond(f"<@{entry_data['userid']}> has a {entry_data['card']} {entry_data['version']} available!",ephemeral=True)
                            else:
                                await ctx.respond(f"<@{entry_data['userid']}> has a {card['card']} available!",ephemeral=True)
        for card in database['users'][f"{ctx.author.id}"]["have"]:
            if card['card'] in database['cards']["want"]:
                for entry_id, entry_data in database['cards']['want'][card['card']].items():
                    if entry_data["userid"] != card["userid"]:
                        if(entry_data['trade_only']==False or card["sell_only"] == False):
                            if(entry_data['version_strict_search']==True):
                                if(entry_data['version'] == card['version']):
                                    await ctx.respond(f"<@{entry_data['userid']}> may be interested in your {card['card']} {card['version']}!", ephemeral=True)
                            else:
                                await ctx.respond(f"<@{entry_data['userid']}> may be interested in your {card['card']}!", ephemeral=True)

def process(userid, data, options):
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
                    entry["version_strict_search"] = options["version_strict_search"]
                    entry["trade_only"] = options["trade_only"]
                if method=="have":
                    entry["sell_only"] = options["sell_only"]
                database['users'][f"{userid}"][method].append(entry)
                # add the card request to the cards index.
                if card not in database['cards'][method]:
                    database['cards'][method][card] = {}
                database['cards'][method][card][uid] = entry
    write_database()

# --------------------------

base_dir = os.path.dirname(__file__)
database_path = f"{base_dir}/database.json"
database={}

def load_database():
    global database
    if not os.path.exists(database_path):
        database = {"users":{},"cards":{"want":{},"have":{}}}
        write_database()
    else:
        with open(database_path, "r") as db:
            database = json.load(db)
    print("database loaded.")

def write_database():
    with open(database_path, "w") as db:
        json.dump(database,db,indent=4)
    print("writing database")

load_dotenv()

load_database()
if(database):
    bot.run(os.getenv('TOKEN'))
else:
    raise BaseException("Could not load database")