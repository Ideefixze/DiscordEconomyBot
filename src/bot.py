# bot.py
import os
import keys
import discord
from discord.ext import commands
import sqlite3
import tenorpy
import random

CURRENCY = "ZS"

TOKEN = keys.token

tenor = tenorpy.Tenor()
bot = commands.Bot(command_prefix='$')


client = discord.Client()
dbconnect = sqlite3.connect('database.db')

dbconnect.execute(
'''
CREATE TABLE IF NOT EXISTS Teams (
    id INTEGER PRIMARY KEY,
    name NVARCHAR(50),
    funds INTEGER,
    closed BOOLEAN DEFAULT 0,
    channel INTEGER
);
 ''')

dbconnect.execute(
'''
CREATE TABLE IF NOT EXISTS Players (
    id INTEGER PRIMARY KEY,
    name NVARCHAR(50),
    team_id INTEGER,
    FOREIGN KEY (team_id)
        REFERENCES Teams (id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);''')
dbconnect.commit()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

class GMCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='createteam', help="Creates a new team.")
    async def create_team_command(self, ctx, team_name, funds):
        role = discord.utils.find(lambda r: r.name == 'GM', ctx.message.guild.roles)
        if not role:
            await ctx.send(f"You don't have \'GM\' role.")
            return
        
        dbconnect.execute(f"INSERT INTO Teams (name, funds) VALUES (\'{team_name}\', {funds})")
        dbconnect.commit()
        await ctx.send(f"You have created {team_name} with starting {funds} {CURRENCY}." )

    @commands.command(name='setchannel', help="Sets a primary channel for a team.")
    async def set_channel_command(self, ctx, team_name):
        role = discord.utils.find(lambda r: r.name == 'GM', ctx.message.guild.roles)
        if not role:
            await ctx.send(f"You don't have \'GM\' role.")
            return

        t = team_by_team_name(team_name)
        if not t:
            await ctx.send(f"Team **{team_name}** does not exist.")
            return
        
        dbconnect.execute(f"UPDATE Teams SET channel={ctx.message.channel.id} WHERE name=\'{team_name}\'")
        dbconnect.commit()
        
        await ctx.send(f"You have set channel for {team_name} team. All `pay` commands to this team will be shown here." )

    @commands.command(name='earn', help="Adds some portion of money to the team's account.")
    async def earn_command(self, ctx, value, team, *description):

        role = discord.utils.find(lambda r: r.name == 'GM', ctx.message.guild.roles)
        if not role:
            await ctx.send(f"You don't have \'GM\' role.")
            return

        desc = " ".join(description[:])
        value = int(value)
        t = team_by_team_name(team)
        if not t:
            await ctx.send(f"Team **{team}** does not exist.")
        else:
            old = t[2]
            if value > 0:
                dbconnect.execute(f"UPDATE Teams SET funds=funds+{value} WHERE id={t[0]}")
                dbconnect.commit()
                t = team_by_team_name(team)
                await ctx.send(f"**{t[1]}** received: **{value} {CURRENCY}**\nDescription: *{desc}*\n**{t[1]}**  had: **{old} {CURRENCY}**\nNow **{t[1]}** have: **{t[2]} {CURRENCY}**")
            if value < 0:
                dbconnect.execute(f"UPDATE Teams SET funds=funds-{abs(value)} WHERE id={t[0]}")
                dbconnect.commit()
                t = team_by_team_name(team)
                await ctx.send(f"**{t[1]}** has lost: **{value} {CURRENCY}**\nDescription: *{desc}*\n**{t[1]}**  had: **{old} {CURRENCY}**\nNow **{t[1]}** have: **{t[2]} {CURRENCY}**")

class PlayerCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="register", help="Sign up for WW Economy!")
    async def register_command(self, ctx, *name):
        r = already_registered(ctx.author.id)
        character_name = " ".join(name)
        if not r:
            dbconnect.execute(f"INSERT INTO Players (id, name) VALUES ({ctx.author.id}, \'{character_name}\')")
            dbconnect.commit()
            r = already_registered(ctx.author.id)
            if r:
                await ctx.send(f"{character_name} have been registered!")
            else:
                await ctx.send("Some problem occured!")
        else:
            await ctx.send(f"You have an character: **{r[0]}**")

    @commands.command(name="delete", help="Deletes you character.")
    async def delete_command(self, ctx):
        r = already_registered(ctx.author.id)
        if r:
            dbconnect.execute(f"DELETE FROM Players WHERE id={ctx.author.id}")
            dbconnect.commit()
            r = already_registered(ctx.author.id)
            if not r:
                await ctx.send(f"You have deleted your character!")
            else:
                await ctx.send("Some problem occured!")
        else:
            await ctx.send(f"You dont have a character that can be deleted.")
        

    @commands.command(name='join', help="Joins a team.")
    async def join_command(self, ctx, team):
        t = team_by_player_id(ctx.author.id)
        if not t:
            t = team_by_team_name(team)
            #If closed...
            if(t[3]==True):
                await ctx.send(f"This team is closed and you can't join it.")
                return

            dbconnect.execute(f"UPDATE Players SET team_id = (SELECT id FROM Teams WHERE name = \'{team}\') WHERE id={ctx.author.id}")
            dbconnect.commit()
            t = team_by_player_id(ctx.author.id)
            if t:
                await ctx.send(f"You have joined **{t[1]}**")
            else:
                await ctx.send(f"Some problem occured! Does **{team}** team exist?")
        else:
            await ctx.send(f"You are already a member of **{t[1]}**. If you want to change a team, contact the GM.")

    @commands.command(name='close', help="Closes your team, so none can join.")
    async def close_command(self, ctx):
        t = team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send(f"You can't close a team, because you don't have a team!")
        else:
            dbconnect.execute(f"UPDATE Teams SET closed = true WHERE id={t[0]}")
            dbconnect.commit()
            await ctx.send(f"**{t[1]}** has been closed!")

    @commands.command(name='open', help="Reopens your team, so other people may join.")
    async def open_command(self, ctx):
        t = team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send(f"You can't open a team, because you don't have a team!")
        else:
            dbconnect.execute(f"UPDATE Teams SET closed = false WHERE id={t[0]}")
            dbconnect.commit()
            await ctx.send(f"**{t[1]}** has been opened!")

    @commands.command(name='myteam', help="Shows your team info.")
    async def my_team_command(self, ctx):
        t = team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send("You are not a member of any team...")
        else:
            await ctx.send(f"You are a member of **{t[1]}** and you have **{t[2]} {CURRENCY}**.\nCurrent members of your team:")
            await self.show_member_list(ctx, t[1])

    @commands.command(name='team', help="Shows info of given team.")
    async def team_command(self, ctx, team):
        t = team_by_team_name(team)
        if not t:
            await ctx.send(f"Can't find a team named **{team}**")
        else:
            await ctx.send(f"**{t[1]}** possess **{t[2]} {CURRENCY}**.\nCurrent team members of this team:")
            await self.show_member_list(ctx, team)

    @commands.command(name='allteams', help="Shows info of given team.")
    async def allteams_command(self, ctx):
        c = dbconnect.cursor()
        c.execute("SELECT * FROM Teams")
        fetch = c.fetchall()
        c.close()
        await ctx.send(f"There are **{len(fetch)}** teams in the game.\n\n")
        for team in fetch:
            await self.team_command(ctx, team[1])


    async def show_member_list(self, ctx, team_name):
        t = team_by_team_name(team_name)
        t_members = all_team_members(t[0])
        member_list = ""
        for member in t_members:
            member_list+=f"`{member[0]}`\n"
        if len(t_members)==0:
            await ctx.send("No members...")
        else:
            await ctx.send(f"{member_list}")


    @commands.command(name='guide', help="Short tutorial on how to use this bot.")
    async def guide_command(self, ctx):
        await ctx.send("Use `$register <character_name>` to register your character in the database.\nThen `$join <team_name>` to join a team (it must be created earlier by a GM)\nYou now have access to all team-related commands such as `$pay` and `$spend`. If you want to change a team, delete your character and join a team again.");


    @commands.command(name='spend', help="Removes some portion of money from your team's account.")
    async def spend_command(self, ctx, value, *args):
        desc = " ".join(args[:])
        value = int(value)
        if value<0:
            await ctx.send("Don't do that!")
            return

        t = team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send("You are not a member of any team...")
        else:
            if t[2] >= value:
                old = t[2]
                dbconnect.execute(f"UPDATE Teams SET funds=funds-{value} WHERE id={t[0]}")
                dbconnect.commit()
                t = team_by_player_id(ctx.author.id)
                await ctx.send(f"**{t[1]}** spent: **{value} {CURRENCY}**\nDescription: *{desc}*\n**{t[1]}**  had: **{old} {CURRENCY}**\nNow **{t[1]}** have: **{t[2]} {CURRENCY}**")
    
                #await ctx.send(tenor.random(tenor_random_tag()))

            else:
                await ctx.send(f"Not enough {CURRENCY}...")


    @commands.command(name='pay', help="Sends some portion of money from your team's account to other team.")
    async def pay_command(self, ctx, value, other_team, *description):
        desc = " ".join(description[:])
        value = int(value)
        if value<=0:
            await ctx.send("Don't do that!")
            return
        ot = team_by_team_name(other_team)
        if  ot==None:
            await ctx.send(f"Team **{other_team}** does not exist.")
            return

        t = team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send("You are not a member of any team...")
        else:
            if t[1] == other_team:
                await ctx.send("Target of payment must be a different team.")
                return
            if t[2] >= value:
                old = t[2]
                old_ot = ot[2]
                dbconnect.execute(f"UPDATE Teams SET funds=funds-{value} WHERE id={t[0]}")
                dbconnect.execute(f"UPDATE Teams SET funds=funds+{value} WHERE name=\'{other_team}\'")
                dbconnect.commit()
                t = team_by_player_id(ctx.author.id)
                ot = team_by_team_name(other_team)
                mess = f"**{t[1]}** paid **{value} {CURRENCY}** to **{other_team}**\nDescription: *{desc}*\n{t[1]} had: **{old} {CURRENCY}**\n{t[1]} now have: **{t[2]} {CURRENCY}**\n\n{ot[1]} had: **{old_ot} {CURRENCY}**\n{ot[1]} now have: **{ot[2]} {CURRENCY}**"
                await ctx.send(mess)
                await notify_team_channel(other_team,mess)
                if ctx.channel.id!=t[4]:
                    await notify_team_channel(t[1],mess)
                
            else:
                await ctx.send(f"Not enough {CURRENCY}...")
    

#Other functions
def team_by_team_name(name):
    c = dbconnect.cursor()
    c.execute(f"SELECT * FROM Teams WHERE name=\'{name}\'")
    fetch = c.fetchone()
    c.close()
    return fetch

def team_by_team_id(id):
    c = dbconnect.cursor()
    c.execute(f"SELECT * FROM Teams WHERE id={id}")
    fetch = c.fetchone()
    c.close()
    return fetch


def team_by_player_id(id):
    c = dbconnect.cursor()
    c.execute(f"SELECT T.* FROM Players P JOIN Teams T ON P.team_id=T.id WHERE P.id={id}")
    fetch = c.fetchone()
    c.close()
    return fetch

def all_team_members(t_id):
    c = dbconnect.cursor()
    c.execute(f"SELECT name FROM Players WHERE team_id={t_id}")
    fetch = c.fetchall()
    c.close()
    return fetch

def already_registered(id):
    c = dbconnect.cursor()
    c.execute(f"SELECT name FROM Players WHERE id={id}")
    fetch = c.fetchone()
    c.close()
    return fetch

def tenor_random_tag():
    tags = ['money']
    return random.choice(tags)

async def notify_team_channel(team_name, text):
    t = team_by_team_name(team_name)
    c = bot.get_channel(t[4])
    if c:
        await c.send(text)
    else:
        print(t)


bot.add_cog(GMCommands(bot))
bot.add_cog(PlayerCommands(bot))
bot.run(TOKEN)
client.run(TOKEN)