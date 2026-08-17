import math
import os
import random
import re
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands

# --------------------------------------------------
# 1. Renderスリープ防止用Webサーバー
# --------------------------------------------------
app = Flask("")


@app.route("/")
def home():
    return "Bot is running!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# --------------------------------------------------
# 2. Discord Botの基本設定
# --------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# 小数点第3位以降を切り捨てる関数
def truncate_2_decimals(val):
    if isinstance(val, (int, float)):
        # 100倍して端数を切り捨て、100で割ることで第2位まで保持
        truncated = math.trunc(val * 100) / 100
        if truncated.is_integer():
            return int(truncated)
        return truncated
    return val


# --------------------------------------------------
# 3. ダイス＋計算 一体型コマンド (!r または !roll)
# --------------------------------------------------
@bot.command(aliases=["r"])
async def roll(ctx, *, expr: str):
    try:
        original_expr = expr
        expr_clean = expr.lower().replace(" ", "")

        # ダイス表記 (例: 2d6, 1d100) の検索と実行
        dice_pattern = r"(\d+)d(\d+)"
        dice_matches = re.findall(dice_pattern, expr_clean)

        dice_details = []
        eval_expr = expr_clean

        for count_str, sides_str in dice_matches:
            count = int(count_str)
            sides = int(sides_str)

            if count > 50 or sides > 1000:
                await ctx.send(
                    "エラー: ダイスは50個、面数は1000面までにしてください。"
                )
                return

            rolls = [random.randint(1, sides) for _ in range(count)]
            total_roll = sum(rolls)

            dice_details.append(
                f"{count}d{sides}[{', '.join(map(str, rolls))}]"
            )

            # 式の中のダイス表記を合計値に置き換える
            eval_expr = re.sub(
                rf"{count}d{sides}", str(total_roll), eval_expr, count=1
            )

        # 安全な数式かどうかのセキュリティチェック
        if not re.match(r"^[0-9+\-*/().\s]+$", eval_expr):
            await ctx.send(
                "エラー: 使用できるのはダイス表記(2d6など)と数値・記号(+ - * / ())のみです。"
            )
            return

        # 計算実行と切り捨て処理
        raw_result = eval(eval_expr)
        final_result = truncate_2_decimals(raw_result)

        # 結果メッセージの生成
        details_str = (
            f" (`{' / '.join(dice_details)}`)" if dice_details else ""
        )
        await ctx.send(
            f"🎲 **実行結果**: `{original_expr}`\n"
            f"┗ 展開: `{eval_expr}`{details_str}\n"
            f"┗ 最終結果: **{final_result}**"
        )

    except ZeroDivisionError:
        await ctx.send("エラー: 0で割ることはできません。")
    except Exception:
        await ctx.send("エラー: 式を正しく計算できませんでした。")


# --------------------------------------------------
# 4. 起動
# --------------------------------------------------
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
