from disnake.ext.commands import InteractionBot
from dotenv import load_dotenv
from os import getenv
from aiosqlite import connect, Cursor
from disnake import CommandInteraction
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uvicorn import Config, Server

load_dotenv()

bot = InteractionBot()
app = FastAPI()
templates = Jinja2Templates(directory="./templates")


class UpdateModel(BaseModel):
    value: str
    guild_id: str


@bot.slash_command(name="test")
async def _test(inter: CommandInteraction):
    async with connect("db.sqlite") as db:
        async with db.cursor() as cursor:
            cursor: Cursor

            await cursor.execute("CREATE TABLE IF NOT EXISTS dashboard(guild_id INT NOT NULL, value TEXT)")
            await db.commit()

            await cursor.execute("SELECT value FROM dashboard WHERE guild_id=?", (inter.guild_id,))
            value = await cursor.fetchone()

            if value is None:
                value = "Значение пустое."
            else:
                value = value[0]

            return await inter.send(value)


@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.put("/dashboard")
async def dashboard_update(model: UpdateModel):
    async with connect("db.sqlite") as db:
        async with db.cursor() as cursor:
            cursor: Cursor

            await cursor.execute("CREATE TABLE IF NOT EXISTS dashboard(guild_id INT NOT NULL, value TEXT)")
            await db.commit()

            await cursor.execute("SELECT value FROM dashboard WHERE guild_id=?", (int(model.guild_id),))
            value = await cursor.fetchone()

            if value is None:
                await cursor.execute("INSERT INTO dashboard VALUES(?, ?)", (int(model.guild_id), model.value,))
                await db.commit()
            else:
                await cursor.execute("UPDATE dashboard SET value=? WHERE guild_id=?", (model.value, int(model.guild_id),))
                await db.commit()

            return {"ok": True}


configuration = Config(app=app, host="localhost", port=8000)
server = Server(configuration)

bot.loop.create_task(server.serve())
bot.run(getenv("TOKEN"))
