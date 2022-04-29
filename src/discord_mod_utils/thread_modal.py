import discord

from .manager import ModerationManager
from .views import ModInviteViewContainer


class ModThreadCreationModal(discord.ui.Modal):
    """The modal for creating a new moderation case thread"""

    def __init__(
        self,
        message: discord.Message,
        thread_channel: int,
        manager: ModerationManager,
        *args,
        **kwargs,
    ) -> None:
        """Initialize moderation case creation modal"""
        self.__message = message
        self.__thread_channel = thread_channel
        self.__manager = manager
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(
                label="Short description",
                placeholder="Will be used as the name for the thread",
            )
        )
        self.add_item(
            discord.ui.InputText(
                label="Longer description",
                style=discord.InputTextStyle.long,
                placeholder="Will be used as the introduction message",
                required=False,
            )
        )

    @property
    def __title(self):
        return self.children[0].value

    @property
    def __description(self):
        """If we don't have the description, just use the title"""
        if self.children[1].value:
            return self.children[1].value
        return self.__title

    async def callback(self, interaction: discord.Interaction):
        """Create a moderation thread"""
        response = await interaction.response.send_message(
            "Setting up the thread...", ephemeral=True
        )

        if interaction.guild is None:
            await response.edit_original_message(
                content="Can't determine a moderator cases channel outside of a guild"
            )
            return
        thread = await self.__manager.create_thread(
            title=self.__title,
            description=self.__description,
            channel_id=self.__thread_channel,
        )
        if thread is None:
            await response.edit_original_message(content="Failed to create the thread")
            return
        member = await interaction.guild.fetch_member(self.__message.author.id)
        await self.__manager.populate_thread(
            thread, interaction.user, member, self.__message
        )

        mods = await self.__manager.get_active_mods(self.__message)
        await response.edit_original_message(
            content=f"Created a new moderation thread: {thread.mention}",
            view=ModInviteViewContainer(mods=mods, thread=thread).view,
        )
