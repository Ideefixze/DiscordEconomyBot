from discord.ext import commands
import database

class PlayerCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="register", help="Sign up for WW Economy!")
    async def register_command(self, ctx, *name):
        
        #Find player by user.id
        r = database.player_by_player_id(ctx.author.id)
        character_name = " ".join(name)
        #If they dont exist then register
        if not r:
            database.dbconnect.execute(f"INSERT INTO Players (id, name) VALUES ({ctx.author.id}, \'{character_name}\')")
            database.dbconnect.commit()
            #Find them again, if found: success
            r = database.player_by_player_id(ctx.author.id)
            if r:
                await ctx.send(f"{character_name} have been registered!")
            else:
                await ctx.send("Some problem occured!")
        else:
            await ctx.send(f"You have an character: **{r[0]}**")

    @commands.command(name="delete", help="Deletes you character.")
    async def delete_command(self, ctx):
        #Find player by user.id
        r = database.player_by_player_id(ctx.author.id)
        #If they exist, delete
        if r:
            database.dbconnect.execute(f"DELETE FROM Players WHERE id={ctx.author.id}")
            database.dbconnect.commit()
            #If can't find: success
            r = database.player_by_player_id(ctx.author.id)
            if not r:
                await ctx.send(f"You have deleted your character!")
            else:
                await ctx.send("Some problem occured!")
        else:
            await ctx.send(f"You dont have a character that can be deleted.")
        

    @commands.command(name='join', help="Joins a team.")
    async def join_command(self, ctx, team):
        #Find if player has a team
        t = database.team_by_player_id(ctx.author.id)
        if not t:
            #Find team that player wants to join to
            t = database.team_by_team_name(team)
            #If closed...
            if(t[3]==True):
                await ctx.send(f"This team is closed and you can't join it.")
                return
            #If not closed...
            database.dbconnect.execute(f"UPDATE Players SET team_id = (SELECT id FROM Teams WHERE name = \'{team}\') WHERE id={ctx.author.id}")
            database.dbconnect.commit()

            #Find team of this player and show him team that he just joined to
            t = database.team_by_player_id(ctx.author.id)
            if t and t[1]==team:
                await ctx.send(f"You have joined **{t[1]}**")
            else:
                await ctx.send(f"Some problem occured! Does **{team}** team exist?")
        else:
            await ctx.send(f"You are already a member of **{t[1]}**. If you want to change a team, contact the GM.")

    @commands.command(name='close', help="Closes your team, so none can join.")
    async def close_command(self, ctx):
        #Find your team
        t = database.team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send(f"You can't close a team, because you don't have a team!")
        else:
            #Close the team that you belong to
            database.set_team_closed(1,t[0])
            await ctx.send(f"**{t[1]}** has been closed!")

    @commands.command(name='open', help="Reopens your team, so other people may join.")
    async def open_command(self, ctx):
        #Find your team
        t = database.team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send(f"You can't open a team, because you don't have a team!")
        else:
            #Open the team that you belong to
            database.set_team_closed(0,t[0])
            await ctx.send(f"**{t[1]}** has been opened!")

    @commands.command(name='myteam', help="Shows your team info.")
    async def my_team_command(self, ctx):
        #Get team of player making this command
        t = database.team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send("You are not a member of any team...")
        else:
            #Show info of that team
            await ctx.send(f"You are a member of **{t[1]}** and you have **{t[2]} {database.CURRENCY}**.\nCurrent members of your team:")
            await self.show_member_list(ctx, t[1])

    @commands.command(name='team', help="Shows info of given team.")
    async def team_command(self, ctx, team):
        #Get team by the name
        t = database.team_by_team_name(team)
        if not t:
            await ctx.send(f"Can't find a team named **{team}**")
        else:
            #Show info of that team
            await ctx.send(f"**{t[1]}** possess **{t[2]} {database.CURRENCY}**.\nIs closed?: {t[3]}\nCurrent team members of this team:")
            await self.show_member_list(ctx, team)

    @commands.command(name='allteams', help="Shows info of given team.")
    async def allteams_command(self, ctx):
        #Using cursor get all teams and show info
        c = database.dbconnect.cursor()
        c.execute("SELECT * FROM Teams")
        fetch = c.fetchall()
        c.close()
        await ctx.send(f"There are **{len(fetch)}** teams in the game.\n\n")
        for team in fetch:
            await self.team_command(ctx, team[1])


    async def show_member_list(self, ctx, team_name):
        #Prints out all members by team name
        #Get team id
        t = database.team_by_team_name(team_name)
        #Get all members by team id
        t_members = database.all_team_members(t[0])
        #Construct string and print
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
        #Find team by user id
        t = database.team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send("You are not a member of any team...")
        else:
            #If team has funds, remove them
            if t[2] >= value:
                old = t[2]
                database.dbconnect.execute(f"UPDATE Teams SET funds=funds-{value} WHERE id={t[0]}")
                database.dbconnect.commit()
                t = database.team_by_player_id(ctx.author.id)
                await ctx.send(f"**{t[1]}** spent: **{value} {database.CURRENCY}**\nDescription: *{desc}*\n**{t[1]}**  had: **{old} {database.CURRENCY}**\nNow **{t[1]}** have: **{t[2]} {database.CURRENCY}**")
            else:
                await ctx.send(f"Not enough {database.CURRENCY}...")


    @commands.command(name='pay', help="Sends some portion of money from your team's account to other team.")
    async def pay_command(self, ctx, value, other_team, *description):
        desc = " ".join(description[:])
        value = int(value)
        if value<=0:
            await ctx.send("Don't do that!")
            return
        #Find if other team exist...
        ot = database.team_by_team_name(other_team)
        if  ot==None:
            await ctx.send(f"Team **{other_team}** does not exist.")
            return

        #Find if player belongs to a team
        t = database.team_by_player_id(ctx.author.id)
        if not t:
            await ctx.send("You are not a member of any team...")
        else:
            if t[1] == other_team:
                await ctx.send("Target of payment must be a different team.")
                return
            #If team has funds, send them to the other team
            if t[2] >= value:
                old = t[2]
                old_ot = ot[2]
                database.dbconnect.execute(f"UPDATE Teams SET funds=funds-{value} WHERE id={t[0]}")
                database.dbconnect.execute(f"UPDATE Teams SET funds=funds+{value} WHERE name=\'{other_team}\'")
                database.dbconnect.commit()
                t = database.team_by_player_id(ctx.author.id)
                ot = database.team_by_team_name(other_team)
                mess = f"**{t[1]}** paid **{value} {database.CURRENCY}** to **{other_team}**\nDescription: *{desc}*\n{t[1]} had: **{old} {database.CURRENCY}**\n{t[1]} now have: **{t[2]} {database.CURRENCY}**\n\n{ot[1]} had: **{old_ot} {database.CURRENCY}**\n{ot[1]} now have: **{ot[2]} {database.CURRENCY}**"
                await ctx.send(mess)
                await self.notify_team_channel(other_team,mess)
                if ctx.channel.id!=t[4]:
                    await self.notify_team_channel(t[1],mess)
                
            else:
                await ctx.send(f"Not enough {database.CURRENCY}...")
    
    async def notify_team_channel(self, team_name, text):
        '''
        Notifies a team channel with a message (text).
        '''
        t = database.team_by_team_name(team_name)
        c = self.bot.get_channel(t[4])
        if c:
            await c.send(text)    