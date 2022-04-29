from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Optional
from typing import Union

import discord
import humanize

from .config import Config
from .views import UserActionsView


class ModerationManager:
    """A class that actually manages all of the actions"""

    def __init__(self, bot: discord.Bot, config: Config):
        self.bot = bot
        self.config = config

    def datetime_to_text(self, time: datetime) -> str:
        """Convert a datetime.datetime to a human-readable representation"""
        ago = humanize.naturaltime(time, when=datetime.now(timezone.utc))
        absolute = time.strftime("%H:%M:%S, %d %b, %Y")
        return f"{ago}; {absolute}"

    def form_message_info_embed(
        self, message: discord.Message, requested_by: discord.Member
    ) -> discord.Embed:
        """Create a message info embed"""
        embed = discord.Embed(title="Message info")
        embed.add_field(name="Moderator", value=requested_by.mention, inline=True)
        embed.add_field(
            name="Original message",
            value=f"[link]({message.jump_url})",
            inline=True,
        )
        embed.add_field(
            name="Original author", value=message.author.mention, inline=True
        )
        embed.add_field(
            name="Sent", value=self.datetime_to_text(message.created_at), inline=True
        )
        if message.edited_at:
            embed.add_field(
                name="Edited",
                value=self.datetime_to_text(message.edited_at),
                inline=True,
            )
        if isinstance(message.channel, discord.TextChannel):
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        return embed

    def form_user_info_embed(
        self,
        member: Union[discord.User, discord.Member],
        channel=None,
        short: bool = False,
    ) -> discord.Embed:
        """Create a member info embed"""
        user_info = discord.Embed(title="User info")

        user_info.add_field(name="ID", value=str(member.id), inline=True)
        user_info.add_field(
            name="Joined Discord",
            value=self.datetime_to_text(member.created_at),
            inline=True,
        )
        if isinstance(member, discord.Member) and member.joined_at:
            user_info.add_field(
                name="Joined Server",
                value=self.datetime_to_text(member.joined_at),
                inline=True,
            )
        if isinstance(member, discord.Member):
            user_info.add_field(
                name="Roles",
                value=",".join(role.mention for role in member.roles),
                inline=False,
            )
            if not short:
                user_info.add_field(
                    name="Guild permissions",
                    value=", ".join(
                        perm.replace("_", " ").capitalize()
                        for perm, value in member.guild_permissions
                        if value
                    ),
                    inline=False,
                )
                if channel and isinstance(channel, discord.abc.GuildChannel):
                    user_info.add_field(
                        name="Original channel permissions",
                        value=", ".join(
                            perm.replace("_", " ").capitalize()
                            for perm, value in channel.permissions_for(member)
                            if value
                        ),
                        inline=False,
                    )
        name = f"{member.name}#{member.discriminator}"
        if member.avatar:
            user_info.set_thumbnail(url=member.avatar.url)
            user_info.set_author(name=name, icon_url=member.avatar.url)
        else:
            user_info.set_author(name=name)
        return user_info

    async def duplicate_message_into_webhook(
        self, message: discord.Message, thread: discord.Thread, member: discord.Member
    ) -> None:
        """Duplicates a message into a thread using a webhook"""
        channel = thread.parent
        if channel is None:
            return
        hook_id = self.config.get_mod_hook(channel.guild.id)
        webhooks = [
            webhook
            for webhook in await channel.guild.webhooks()
            if webhook.channel_id == channel.id and webhook.id == hook_id
        ]
        if webhooks:
            webhook = webhooks[0]
        else:
            webhook = await channel.create_webhook(
                name="Moderation messages duplicator"
            )
            self.config.set_mod_hook(channel.guild.id, webhook.id)
        await webhook.send(
            content=message.content,
            username=member.display_name,
            avatar_url=member.avatar and member.avatar.url,
            embeds=message.embeds,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=False, replied_user=False
            ),
            thread=thread,
        )

    async def get_active_mods(self, message: discord.Message) -> list[discord.Member]:
        """Given a message, get list of mods who were participating

        Given a message, provided that it is recent, get a list of
        mods who were participating in the conversation. If the
        message is not recent, returns an empty list

        """
        if message.guild is None:
            # There are no mods outside of guilds
            return []
        if (datetime.now(timezone.utc) - message.created_at).total_seconds() > 15 * 60:
            # We are operating on an old message; don't care
            # The limit is arbitrarily set to 15 minutes
            return []
        active_mods = []
        analyzed = []
        async for message in message.channel.history(
            limit=100, after=datetime.now(timezone.utc) - timedelta(seconds=15 * 60)
        ):
            if message.guild is None:
                continue  # so that mypy shuts up
            if message.author.id in analyzed:
                continue  # don't wanna refetch a member
            author = await message.guild.fetch_member(message.author.id)
            analyzed.append(message.author.id)
            if self.config.get_mod_role(message.guild.id) in [
                role.id for role in author.roles
            ]:
                active_mods.append(author)
        return active_mods

    async def create_thread(
        self, title: str, description: str, channel_id: int
    ) -> Optional[discord.Thread]:
        """Creates a modcase thread in a given channel

        Args:
            title: will be used as the name for that thread
            description: will be used as the moderation case summary
            channel_id: the channel to create the thread in

        Returns:
            None if the channel wasn't a discord.TextChannel
            the created thread otherwise

        """
        cases_channel = await self.bot.fetch_channel(channel_id)
        if not isinstance(cases_channel, discord.TextChannel):
            return None
        message: discord.Message = await cases_channel.send(description)
        thread: discord.Thread = await message.create_thread(name=title)
        return thread

    async def populate_thread(
        self,
        thread: discord.Thread,
        requester,
        member: discord.Member,
        message: discord.Message,
    ) -> None:
        """Populate the mod case thread

        Sends the message and user info and replicates the original
        message with a webhook

        Args:
            thread: the thread to post to
            requester: the moderator who requested the ccase
            member: the user being reported
            message: the reported message

        """
        await thread.send(
            embed=self.form_message_info_embed(message, requester),
            view=UserActionsView(member=member, config=self.config),
        )
        await self.duplicate_message_into_webhook(message, thread, member)
        await thread.send(
            embed=self.form_user_info_embed(member, message.channel, True)
        )
