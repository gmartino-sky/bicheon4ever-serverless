#!/usr/bin/env python3
"""
Script para registrar los comandos slash en Discord.
Ejecutar después de desplegar la aplicación.
"""
import requests
import os

DISCORD_TOKEN = "TU_BOT_TOKEN"
APP_ID = "TU_APPLICATION_ID"

url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}

commands = [
    {"name": "usar", "description": "Configura el canal para noticias", "options": [
        {"name": "canal", "description": "Canal de Discord", "type": 7, "required": True}
    ]},
    {"name": "verificar-parche", "description": "Muestra el último Patch Note"},
    {"name": "verificar-evento", "description": "Muestra el último Evento"},
    {"name": "verificar-noticia", "description": "Muestra la última Noticia"},
    {"name": "estado-bot", "description": "Muestra el estado del bot"}
]

for cmd in commands:
    requests.post(url, headers=headers, json=cmd)
    print(f"✅ Registrado: /{cmd['name']}")
