import PIL
import discord
import random
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
from PIL import Image, ImageEnhance, ImageFont, ImageDraw 
import io
import re

randomPrefix = "madsmonster"
uploadPrefix = "upload"


contentFlags = {
    "v" : "visualFile",
    "t" : "toptext",
    "b" : "bottomtext",
    "s" : "soundFile",
}

contentPaths = {
    'v': 'visuals',
    't': 'toptexts',
    'b': 'bottomtexts',
    's': 'sounds',
    'm': 'Upload/Memes'
}

visualFileExtensions = ["png","jpg","gif"]
soundFileExtensions = ["mp3","wav"]
typeToExtions = {
    "visual" : visualFileExtensions,
    "sound" : soundFileExtensions
}

load_dotenv()
testing =  os.getenv('TESTING') == "True"
apihost = os.getenv("API_HOST")
protocol = os.getenv("PROTOCOL")

bot = commands.Bot(command_prefix='$' if not testing else '?')

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

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

def openImageFromUrl(url):
    return Image.open(io.BytesIO(requests.get(url).content))

async def extract(ctx, contentType, strict):
    if contentType == 't' or contentType == 'b' :
        text = re.search("\".*?\"",ctx.message.content)
        if not text:
            if strict:
                await ctx.send("Error: Include the top or bottom text in \"\" ")
                return None
            else:
                return ""

        text = text.group(0)[1:-1]
        if len(text) > 100:
            await ctx.send('Error: Text is too long')
            return None

        ctx.message.content = re.sub(text,"",ctx.message.content,1)
        return text

    elif contentType == 'v' or contentType == 's':
        if not ctx.message.attachments:
            #TODO graceful fail proper return value for files
            if strict:
                await ctx.send("No visual or Sound file found")
            return None

        #TODO handle visual and sound at the same time
        fp = io.BytesIO()
        await ctx.message.attachments[0].save(fp)
        return (ctx.message.attachments[0].filename,fp, ctx.message.attachments[0].content_type)
    else:
        await ctx.send('Error: No such content type ' + contentType)
        return None

def randomize(img):
    
    chance = 0
    
    if chance == 3:
        print("brightened")
        filter = ImageEnhance.Brightness(img)
        img = filter.enhance(5)
    elif chance == 2:
        print("rotated")
        img = img.rotate(90)
    elif chance == 0:
        print("test")
        img = ImageEnhance.Brightness(img).enhance(5)
        img = ImageEnhance.Sharpness(img).enhance(5)
        img = ImageEnhance.Color(img).enhance(500)
        emoji = openImageFromUrl("https://server.tobloef.com/faces/random.png")
        emoji = emoji.transpose(PIL.Image.FLIP_LEFT_RIGHT)
        emoji.resize((50,50),Image.ANTIALIAS)
        img.paste(emoji,(250,50))
    else:
        print("flipped")
        img = img.transpose(PIL.Image.FLIP_LEFT_RIGHT)
    return img

@bot.command()
async def upload(ctx, *args):

        files = {}
        body = {}
        strict = True

        if args and args[0].startswith("-"):
            contentType = args[0][1:]
        else: 
            contentType = "vtb"
            strict = False

        if len(contentType) > 1: 
            if 'v' not in contentType:
                return await ctx.send('Error: Multipart memes must have a visual')
            
            #ugly adaption hack for mads.monster, it expects toptext and bottomtext to be "" if it's not included
            body['toptext'] = ""
            body['bottomtext'] = ""
            path = contentPaths['m']

        else:
            path = contentPaths[contentType]

        for flag in contentType:
            content = await extract(ctx, flag, strict)
            if content == None:
                if strict:
                    await ctx.send('Error')
                    return
                else:
                    break
            if (flag == 'b' or flag == 't'):
                body[contentFlags[flag]] = content
            else:
                files[contentFlags[flag]] = content

        if len(contentType) > 1 and contentFlags['v'] not in files.keys():
            return await ctx.send('Error: Multipart memes must have a visual')
        response = requests.post("{}://{}/{}".format(protocol,apihost,path),files=files , data=body)

        if(response.status_code == 200):
            await ctx.send('Success')
        else:
            await ctx.send('Error')


        
@bot.command()
async def madsmonster(ctx,*args):
        resp = requests.get("https://api.mads.monster/random/meme").json()
        img = Image.open(requests.get(resp["visual"], stream=True).raw)
        if "-s" in args:
            img = openImageFromUrl("http://clown.mads.monster/capture")
        if img.mode == "P":
            img = img.convert('RGB')
        img = img.resize((400,400),Image.ANTIALIAS)

        if "-r" in args:
            img = randomize(img)
        
        drawer = ImageDraw.Draw(img)
        font = ImageFont.truetype("impact.ttf", 16)

        draw_text(resp["toptext"], font, (0, 25), (400, 50), drawer)
        draw_text(resp["bottomtext"], font, (0, 325), (400, 50), drawer)

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        await ctx.send(file=discord.File(img_bytes, "meme.png"))


ImageFont.load_default()
bot.run(os.getenv('TOKEN'))