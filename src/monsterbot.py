import discord
import os
from dotenv import load_dotenv
import requests
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import io

load_dotenv()

client = discord.Client()

#shamelessly stolen from julian
def split_line(text, font, width):
    returntext = ""
    while text:
        if (font.getsize(text)[0]) < width:
            returntext += text
            break
        for i in range(len(text), 0, -1):
            if (font.getsize(text[:i])[0]) < width:
                if ' ' not in text[:i]:
                    returntext += text[:i] + "-\n"
                    text = text[i:]
                else:
                    for l in range(i, 0, -1):
                        if text[l] == ' ':
                            returntext += text[:l]
                            returntext += "\n"
                            text = text[l + 1:]
                            break
                break
    if len(returntext) > 3 and returntext[-3] == "-":
        returntext = returntext[:-3]
    return returntext

def get_margins(text, font, max_size, drawer):
    text = split_line(text,font,max_size[0])
    width_margin = round((max_size[0] - drawer.textsize(text, font)[0]) / 2)
    height_margin = round((max_size[1] - drawer.textsize(text, font)[1]) / 2)
    return width_margin, height_margin

def draw_text(text,font,pos,max_size,drawer):
        margins = list(get_margins(text,font,max_size,drawer))

        pos = (pos[0] + margins[0],pos[1] + margins[1])        
        drawer.text((pos[0]-1, pos[1]), text, font=font, fill=(0,0,0))
        drawer.text((pos[0]+1, pos[1]), text, font=font, fill=(0,0,0))
        drawer.text((pos[0], pos[1]-1), text, font=font, fill=(0,0,0))
        drawer.text((pos[0], pos[1]+1), text, font=font, fill=(0,0,0))
        drawer.text((pos[0],pos[1]),text,(255,255,255),font=font)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$madsmonster'):
        resp = requests.get("https://api.mads.monster/random/meme").json()
        img = Image.open(requests.get(resp["visual"], stream=True).raw)
        img = img.resize((400,400),Image.ANTIALIAS)
        drawer = ImageDraw.Draw(img)
        font = ImageFont.truetype("impact.ttf", 16)
        draw_text(resp["toptext"], font, (0, 25), (400, 50), drawer)
        draw_text(resp["bottomtext"], font, (0, 325), (400, 50), drawer)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        await message.channel.send(file=discord.File(img_bytes, "meme.png"))

client.run(os.getenv('TOKEN'))