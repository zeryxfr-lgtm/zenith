import os
import discord
from discord.ext import commands
from google import genai
from dotenv import load_dotenv

# 1. Charger les variables d'environnement du fichier .env
load_dotenv()

# 2. Récupérer les clés de manière sécurisée
DISCORD_TOKEN = os.getenv("DISCORD_TOEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Petite sécurité pour vérifier que les clés sont bien chargées
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Erreur : Les clés DISCORD_TOKEN ou GEMINI_API_KEY sont introuvables dans le fichier .env !")

# 3. Initialisation de Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# 4. Initialisation de Discord
intents = discord.Intents.default()
intents.message_content = True  # Obligatoire pour lire le contenu des messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot connecté avec succès en tant que : {bot.user}")

@bot.event
async def on_message(message):
    # Évite que le bot ne se réponde à lui-même
    if message.author == bot.user:
        return

    # Le bot répond si on le mentionne directement
    if bot.user.mentioned_in(message):
        # On nettoie le message pour enlever la mention du bot
        clean_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        if not clean_prompt:
            await message.reply("Tu m'as appelé ? Pose-moi une question après m'avoir mentionné ! 😊")
            return

        async with message.channel.typing():
            try:
                # Appel à l'API de Gemini (modèle 2.0 Flash)
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=clean_prompt,
                )
                
                # Gestion de la limite de caractères de Discord (2000 max)
                reply_text = response.text
                if len(reply_text) > 2000:
                    reply_text = reply_text[:1990] + "\n...(tronqué)"
                
                await message.reply(reply_text)
                
            except Exception as e:
                print(f"Erreur avec l'API Gemini : {e}")
                await message.reply("Désolé, j'ai rencontré une erreur en essayant de réfléchir... 😵‍💫")

    await bot.process_commands(message)

# Lancement du bot
bot.run(DISCORD_TOKEN)
