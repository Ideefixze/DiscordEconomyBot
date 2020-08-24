# bot.py
import os
import keys
import discord
import sqlite3
import random
import database
import playercommands
import gmcommands
from discord.ext import commands


TOKEN = keys.token

bot = commands.Bot(command_prefix='$')
client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


bot.add_cog(gmcommands.GMCommands(bot))
bot.add_cog(playercommands.PlayerCommands(bot))
bot.run(TOKEN)
client.run(TOKEN)