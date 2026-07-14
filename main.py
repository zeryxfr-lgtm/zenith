import os
import discord
from discord.ext import commands
from google import genai
from dotenv import load_dotenv

# 1. Charger les variables d'environnement du fichier .env
load_dotenv()

# 2. Récupérer les clés de manière sécurisée
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Vérification de sécurité pour s'assurer que les clés sont bien lues
if not DISCORD_TOKEN or not GEMINI_API_KEY:
    raise ValueError(
        "Erreur : DISCORD_TOKEN ou GEMINI_API_KEY est introuvable dans le fichier .env !\n"
        "Vérifie que ton fichier .env contient bien ces variables et qu'il est dans le même dossier."
    )

# 3. Initialisation du client Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# 4. Initialisation du bot Discord avec les intentions requises
intents = discord.Intents.default()
intents.message_content = True  # Indispensable pour lire le contenu des messages et y répondre

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("==================================================")
    print(f"🤖 Bot connecté avec succès en tant que : {bot.user}")
    print("==================================================")

@bot.event
async def on_message(message):
    # Évite que le bot ne se réponde à lui-même ou ne crée des boucles infinies
    if message.author == bot.user:
        return

    # Le bot réagit uniquement s'il est directement mentionné
    if bot.user.mentioned_in(message):
        # On extrait le message en retirant la mention du bot (ex: "<@12345> bonjour" -> "bonjour")
        clean_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        # Si l'utilisateur l'a juste tagué sans écrire de texte
        if not clean_prompt:
            await message.reply("Tu m'as appelé ? Pose-moi une question en me mentionnant ! 😊")
            return

        # Effet d'écriture sur Discord pendant que l'IA génère la réponse
        async with message.channel.typing():
            try:
                # Appel à l'API de Gemini (Modèle 2.0 Flash)
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=clean_prompt,
                )
                
                # Récupération du texte généré par Gemini
                reply_text = response.text
                
                # Discord limite chaque message à un maximum de 2000 caractères
                if len(reply_text) > 2000:
                    reply_text = reply_text[:1990] + "\n...(tronqué)"
                
                await message.reply(reply_text)
                
            except Exception as e:
                error_str = str(e)
                
                # Détection et gestion spécifique de l'erreur de quota épuisé ou blocage géographique (429)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print("⚠️ Alerte Quota : L'API Gemini a renvoyé une erreur 429 (Resource Exhausted).")
                    await message.reply(
                        "Oups ! Les quotas de mon API Gemini sont épuisés ou restreints pour le moment. ⏳\n"
                        "Si le bot est hébergé en ligne, cela est souvent dû aux limites de l'offre gratuite "
                        "de Google dans cette zone géographique."
                    )
                else:
                    print(f"Erreur avec l'API Gemini : {e}")
                    await message.reply("Désolé, j'ai rencontré une erreur en essayant de réfléchir... 😵‍💫")

    # Permet de continuer à gérer les autres commandes classiques si tu en ajoutes plus tard
    await bot.process_commands(message)

# Lancement officiel du bot Discord
bot.run(DISCORD_TOKEN)
