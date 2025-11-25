# 🚀 Guía de Deployment Serverless

Esta guía te ayudará a desplegar Bicheon4ever en AWS usando una arquitectura Serverless.

## 📋 Pre-requisitos

1. **AWS CLI** instalado y configurado
2. **SAM CLI** instalado ([Instrucciones](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
3. **Discord Application** configurada ([Portal](https://discord.com/developers/applications))

### Instalar SAM CLI (Mac)
```bash
brew tap aws/tap
brew install aws-sam-cli
```

## 🔧 Configuración Inicial

### 1. Obtener valores de Discord

Ve al [Discord Developer Portal](https://discord.com/developers/applications):

1. Selecciona tu aplicación
2. **General Information** → Copia el **Public Key**
3. **Bot** → Copia el **Token**

Guárdalos en un lugar seguro, los necesitarás durante el deploy.

## 🚀 Deployment

### 1. Build del proyecto
```bash
sam build
```

### 2. Deploy guiado (primera vez)
```bash
sam deploy --guided
```

Te pedirá lo siguiente:
- **Stack Name**: `bicheon-serverless` (o el que prefieras)
- **AWS Region**: `us-east-1` (o tu región preferida)
- **Parameter DiscordPublicKey**: Pega el Public Key de Discord
- **Parameter DiscordToken**: Pega el Token del Bot
- **Confirm changes before deploy**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **InteractionsFunction may not have authorization defined**: `Y` (normal, Discord llama al endpoint público)
- **Save arguments to configuration file**: `Y`

### 3. Configurar Discord

Al finalizar el deploy, SAM mostrará en **Outputs**:
```
InteractionsApiUrl = https://xyz123.execute-api.us-east-1.amazonaws.com/interactions
```

1. Copia esa URL
2. Ve al Discord Developer Portal → Tu App → **General Information**
3. En **Interactions Endpoint URL**, pega la URL
4. Discord verificará la firma automáticamente ✅

### 4. Registrar Comandos Slash

Crea un script `register_commands.py`:

```python
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
```

Ejecuta:
```bash
python3 register_commands.py
```

## ✅ Verificación

1. Invita el bot a tu servidor Discord
2. Ejecuta `/usar #tu-canal` para configurar el canal
3. Ejecuta `/estado-bot` para verificar que funciona
4. Espera 30 minutos para que el scraper corra automáticamente

## 📊 Monitoreo

Ver logs en AWS CloudWatch:
```bash
sam logs -n ScraperFunction --tail
sam logs -n InteractionsFunction --tail
```

## 🔄 Actualizar el Bot

Si haces cambios en el código:
```bash
sam build
sam deploy
```

No necesitas re-configurar los parámetros, SAM los recuerda.

## 💰 Costos

Con el Free Tier de AWS:
- **Lambda**: 1M invocaciones/mes gratis
- **DynamoDB**: 25GB storage + 25 RCU/WCU gratis
- **API Gateway**: 1M requests/mes gratis

**Costo estimado**: $0/mes (dentro del Free Tier permanente)

## 🛡️ Seguridad

- ✅ Verificación de firma de Discord (PyNaCl)
- ✅ Variables de entorno cifradas (AWS SSM/Secrets Manager opcional)
- ✅ IAM roles con permisos mínimos

## 🧹 Eliminar todo (Rollback)

Si quieres eliminar completamente el stack:
```bash
sam delete
```

Esto borrará todas las Lambdas, tablas DynamoDB, y recursos creados.

---

## 🎯 Próximos Pasos

1. Configurar alarmas de CloudWatch para errores
2. Habilitar X-Ray para tracing (opcional)
3. Agregar más comandos según necesites

¡Listo! Tu bot ahora corre 100% Serverless 🐉
