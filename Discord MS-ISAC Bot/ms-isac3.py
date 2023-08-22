import imaplib
import email
import discord
import asyncio
from discord.ext import commands

email_account = "YOUR EMAIL ADDRESS"
email_password = "YOUR APP PASSWORD"
imap_server = "imap.gmail.com"
imap_port = 993
sender_email = "MS-ISAC.Advisory@msisac.org"


discord_token = "YOUR DISCORD BOT TOKEN"
discord_channel_id = CHANNEL ID OF CHANNEL YOU WANT BOT TO POST # Discord Channel ID

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    await check_emails()


async def check_emails():
    seen_messages = set()

    while True:
        try:
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(email_account, email_password)
            mail.select("inbox")
        except imaplib.IMAP4.error as e:
            print(f'Error connecting to the IMAP server: {e}')
            await asyncio.sleep(5)
            continue

        result, data = mail.search(None, f'(UNSEEN FROM "{sender_email}")')
        if result != 'OK':
            print(f'Error searching for emails: {result}')
            mail.logout()
            await asyncio.sleep(5)
            continue

        for num in data[0].split():
            if num in seen_messages:
                continue

            result, data = mail.fetch(num, "(RFC822)")
            if result != 'OK':
                print(f'Error fetching email: {result}')
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.get_payload(decode=True).decode()
                        break
            else:
                content = msg.get_payload(decode=True).decode()

            start_marker = "MS-ISAC ADVISORY NUMBER:"
            end_marker = "RISK:"
            start_index = content.find(start_marker)
            end_index = content.find(end_marker)
            if start_index != -1 and end_index != -1:
                relevant_content = content[start_index + len(start_marker):end_index].strip()
            else:
                relevant_content = content.strip()

            max_length = 1980
            if len(relevant_content) > max_length:
                relevant_content = relevant_content[:max_length - 3] + "..."

            channel = bot.get_channel(discord_channel_id)
            if channel:
                await channel.send("```" + relevant_content + "```")
                await asyncio.sleep(5)

            seen_messages.add(num)

        mail.logout()

        await asyncio.sleep(15)

bot.run(discord_token)