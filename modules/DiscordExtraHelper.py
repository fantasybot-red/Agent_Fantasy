import datetime

from classs import Module, tool
from classs.AIContext import AIContext


class DiscordExtraHelper(Module):

    def format_timestamp(self, date_obj: datetime.datetime):
        return {
            "relative_time": f"<t:{int(date_obj.timestamp())}:R>",
            "full_time": f"<t:{int(date_obj.timestamp())}:F>",
        }

    @tool(
        user_id="User ID"
    )
    async def get_user_info(self, ctx: AIContext, user_id: str):
        """
        Get user information from user ID.
        This function will get user information from user ID.
        - You should embed the result in a nice format.
        - You MUST provide all the information about the user.
        """
        user_info = await ctx.client.fetch_user(user_id)
        guild_info = await ctx.message.guild.fetch_member(user_id)
        print(f"User info: {user_info}, Guild info: {guild_info}")
        if user_info is None:
            return {
                "success": False,
                "reason": "User not found"
            }

        return {
            "success": True,
            "reason": "User get successfully",
            "user_id": user_info.id,
            "user_name": user_info.name,
            "display_name": user_info.global_name,
            "user_discriminator": user_info.discriminator,
            "user_avatar": user_info.display_avatar.url,
            "user_created_at": self.format_timestamp(user_info.created_at),
            "user_bot": user_info.bot,
            "user_spammer": user_info.public_flags.spammer,
            "guild_user_info": {
                "nickname": guild_info.nick,
                "guild_avatar": guild_info.guild_avatar.url if guild_info.guild_avatar else None,
                "joined_at": self.format_timestamp(guild_info.joined_at),
            } if guild_info else None,
            "user_banner": user_info.banner.url if user_info.banner else None,
            "user_badge": [
                k.replace("_", " ").capitalize() for k, v in user_info.public_flags if v
            ]
        }

    @tool()
    async def get_current_guild_info(self, ctx: AIContext):
        """
        Get current guild information.
        This function will get current guild information.
        - You should embed the result in a nice format.
        - You MUST provide all the information about the guild.
        """
        guild_info = ctx.message.guild
        if guild_info is None:
            return {
                "success": False,
                "reason": "Chat not in a guild"
            }
        return {
            "success": True,
            "reason": "Guild get successfully",
            "guild_id": guild_info.id,
            "guild_name": guild_info.name,
            "guild_description": guild_info.description,
            "guild_icon": guild_info.icon.url if guild_info.icon else None,
            "guild_created_at": self.format_timestamp(guild_info.created_at),
            "guild_owner_id": guild_info.owner_id,
            "guild_owner_username": guild_info.owner.name,
            "guild_owner_name": guild_info.owner.global_name,
            "guild_member_count": guild_info.member_count,
            "guild_verification_level": str(guild_info.verification_level),
            "guild_premium_tier": guild_info.premium_tier,
            "guild_premium_subscription_count": guild_info.premium_subscription_count,
            "emojis_count": len(guild_info.emojis),
            "stickers_count": len(guild_info.stickers),
            "channels_count": len(guild_info.channels),
            "roles_count": len(guild_info.roles)
        }

    @tool()
    async def get_current_channel(self, ctx: AIContext):
        """
        Get current chat channel information.
        This function will get current channel information.
        - You should embed the result in a nice format.
        - You MUST provide all the information about the channel.
        """
        channel_info = ctx.message.channel
        return {
            "success": True,
            "reason": "Channel get successfully",
            "channel_id": channel_info.id,
            "channel_name": channel_info.name,
            "channel_type": str(channel_info.type),
            "channel_created_at": self.format_timestamp(channel_info.created_at),
            "channel_position": channel_info.position,
            "channel_nsfw": channel_info.nsfw,
            "channel_slowmode_delay": channel_info.slowmode_delay if channel_info.slowmode_delay else None,
            "channel_description": channel_info.topic,
            "channel_last_message_id": channel_info.last_message_id
        }


async def setup(client):
    await client.add_module(DiscordExtraHelper(client))
