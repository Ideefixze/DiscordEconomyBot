import discord
from discord.ext import commands
import database

class GMCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def has_role(self, ctx):
        '''
        Returns True if ctx sender has a role named 'GM'
        '''
        role = discord.utils.find(lambda r: r.name == 'GM', ctx.message.guild.roles)
        if not role:
            return False
        else:
            return True

    @commands.command(name='createteam', help="Creates a new team.")
    async def create_team_command(self, ctx, team_name, funds):
        if not self.has_role(ctx):
            await ctx.send(f"You don't have \'GM\' role.")
            return

        #Adds a new team into database
        database.dbconnect.execute(f"INSERT INTO Teams (name, funds) VALUES (\'{team_name}\', {funds})")
        database.dbconnect.commit()
        await ctx.send(f"You have created {team_name} with starting {funds} {database.CURRENCY}." )

    @commands.command(name='setchannel', help="Sets a primary channel for a team.")
    async def set_channel_command(self, ctx, team_name):
        if not self.has_role(ctx):
            await ctx.send(f"You don't have \'GM\' role.")
            return
        

        #Find team by team name...
        t = database.team_by_team_name(team_name)
        if not t:
            await ctx.send(f"Team **{team_name}** does not exist.")
            return

        #Set channel where this message has been sent as primary channel for a chosen team
        database.dbconnect.execute(f"UPDATE Teams SET channel={ctx.message.channel.id} WHERE name=\'{team_name}\'")
        database.dbconnect.commit()
        
        await ctx.send(f"You have set channel for {team_name} team. All `pay` commands to this team will be shown here." )

    @commands.command(name='earn', help="Adds some portion of money to the team's account.")
    async def earn_command(self, ctx, value, team, *description):
        if not self.has_role(ctx):
            await ctx.send(f"You don't have \'GM\' role.")
            return

        desc = " ".join(description[:])
        value = int(value)
        #Find team by team name
        t = database.team_by_team_name(team)
        #If it exist...
        if not t:
            await ctx.send(f"Team **{team}** does not exist.")
        else:
            #Add or remove funds from this team...
            old = t[2]
            if value > 0:
                database.dbconnect.execute(f"UPDATE Teams SET funds=funds+{value} WHERE id={t[0]}")
                database.dbconnect.commit()
                t = database.team_by_team_name(team)
                await ctx.send(f"**{t[1]}** received: **{value} {database.CURRENCY}**\nDescription: *{desc}*\n**{t[1]}**  had: **{old} {database.CURRENCY}**\nNow **{t[1]}** have: **{t[2]} {database.CURRENCY}**")
            if value < 0:
                database.dbconnect.execute(f"UPDATE Teams SET funds=funds-{abs(value)} WHERE id={t[0]}")
                database.dbconnect.commit()
                t = database.team_by_team_name(team)
                await ctx.send(f"**{t[1]}** has lost: **{value} {database.CURRENCY}**\nDescription: *{desc}*\n**{t[1]}**  had: **{old} {database.CURRENCY}**\nNow **{t[1]}** have: **{t[2]} {database.CURRENCY}**")