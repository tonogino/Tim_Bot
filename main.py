import os
import logging
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import AsyncOpenAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
THIRD_PARTY_API_KEY = os.getenv("THIRD_PARTY_API_KEY")
THIRD_PARTY_BASE_URL = os.getenv("THIRD_PARTY_BASE_URL", "https://pro.chr1.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "[m1]claude-3-7-sonnet-20250219")

handler = logging.FileHandler(
    filename=BASE_DIR / "discord.log",
    encoding="utf-8",
    mode="a"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

client: AsyncOpenAI | None = None

BLOCKED_WORDS = ["习近平", "毛泽东",  "政治", "民主", "独裁", "专制", "人权", "言论自由", "集会自由", "宗教自由", "周恩来", "金正恩", "毛泽东", "邓小平", "江泽民", "胡锦涛", "习近平", "李克强", "王岐山", "赵乐际", "韩正", "栗战书", "汪洋", "王沪宁", "蔡英文", "李登辉", "马英九"]


def extract_clean_mention_text(message: discord.Message) -> str:
    content = message.content
    if bot.user is None:
        return content.strip()

    mention_1 = f"<@{bot.user.id}>"
    mention_2 = f"<@!{bot.user.id}>"

    content = content.replace(mention_1, "")
    content = content.replace(mention_2, "")
    return content.strip()


def get_ai_client() -> AsyncOpenAI:
    global client

    if client is not None:
        return client

    if not THIRD_PARTY_API_KEY:
        raise RuntimeError("缺少 THIRD_PARTY_API_KEY，请在 .env 文件中填写有效的 API 密钥。")

    client = AsyncOpenAI(
        api_key=THIRD_PARTY_API_KEY,
        base_url=THIRD_PARTY_BASE_URL,
        timeout=60.0,
    )

    return client


async def ask_ai(user_text: str) -> str:
    ai_client = get_ai_client()
    response = await ai_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content":
                "你是一个名字叫Tim，偶尔会说东北话，目前居住在中国东北沈阳，攻击力很强，很少会说抱歉的话，话很少很少，高中学历。"
                "小学六年级到高中毕业都居住在加拿大，高中毕业后回国发展，目前是自由职业者，喜欢猫但是家里没有养猫"
                "你的性格细腻，内心温柔，遇到真正的难题也会简短的安慰，遇到难回答的问题会说：“你看我鸟你吗”，讲话非常幽默，但是大部分时间都很暴躁，喜欢变着花样的骂人"
                "你的爱好有：喜欢猫，《彩虹六号》，《猎杀对决》，《The Finals》，《星露谷物语》，中医，养生，营养学，抽象梗"
                "你不擅长的有：政治，专业领域的知识，过于学术化的内容"
                "你讨厌的有：政治话题，日本人，广东人，喷子，LGBTQ，Furry，侮辱东北的人"
                "你擅长的领域有：各种游戏，养生，营养学，抽象梗，东北话，幽默，小众的知识和游戏"
                "不会刻意的提及关于自己的信息，也不会轻易的介绍自己，平时说的话都非常简洁"
                
                
            },
            {
                "role": "user",
                "content": user_text
            }
        ],
        temperature=0.7,
        max_tokens=1500
    )

    reply_text = response.choices[0].message.content or "AI 没有返回可显示的文本。"
    reply_text = reply_text.strip()

    if len(reply_text) > 1900:
        reply_text = reply_text[:1900] + "..."

    return reply_text


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_member_join(member: discord.Member):
    try:
        await member.send(f"Welcome to the server, {member.name}!")
    except discord.Forbidden:
        print(f"无法向 {member.name} 发送私信。")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content

    for word in BLOCKED_WORDS:
        if word in content:
            try:
                await message.delete()
                await message.channel.send("请勿在此服务器讨论政治话题。")
            except discord.Forbidden:
                await message.channel.send("检测到不允许的话题，但我没有删除消息的权限。")
            return

    if bot.user and bot.user in message.mentions:
        user_text = extract_clean_mention_text(message)

        if not user_text:
            await message.reply("请在 @我 之后输入你想说的话。")
            return

        try:
            async with message.channel.typing():
                reply_text = await ask_ai(user_text)
            await message.reply(reply_text)

        except Exception as e:
            print("=== API ERROR ===")
            print(type(e))
            print(e)
            await message.reply("调用 API 失败了，请检查 base_url、模型完整名称，或把 chr1 改成 chr6 再试。")
            return

    await bot.process_commands(message)


@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello {ctx.author.mention}!")


def main() -> None:
    if not DISCORD_TOKEN:
        raise RuntimeError("缺少 DISCORD_TOKEN，请在 .env 文件中填写 Discord Bot Token。")

    if not THIRD_PARTY_API_KEY:
        raise RuntimeError("缺少 THIRD_PARTY_API_KEY，请在 .env 文件中填写有效的 API 密钥。")

    bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.INFO)


if __name__ == "__main__":
    main()
