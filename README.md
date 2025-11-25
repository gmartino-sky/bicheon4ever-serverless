# 🐉 Bicheon4ever Serverless - Bot de Discord para MIR4

Bot automatizado de Discord que monitorea el foro oficial de MIR4 y notifica instantáneamente sobre nuevos **patch notes**, **avisos** y **eventos**, con traducción automática a español, portugués y chino.

Ahora migrado a una arquitectura **Serverless** en AWS para mayor eficiencia y escalabilidad.

## ✨ Características

- ☁️ **Arquitectura Serverless**: Ejecutado en AWS Lambda, sin servidores que mantener.
- 🔍 **Monitoreo Automático**: Revisa el foro de MIR4 cada 30 minutos (EventBridge).
- 🌐 **Traducción Multiidioma**: Botones interactivos para traducir a Español (🇪🇸), Portugués (🇵🇹) y Chino (🇨🇳).
- 📝 **Resúmenes Inteligentes**: Genera resúmenes automáticos, limpios y formateados.
- 💬 **Comandos Slash**: Interfaz moderna con comandos `/` de Discord.
- � **Persistencia**: Configuración y estado guardados en DynamoDB.
- 🛡️ **Seguridad**: Verificación de firmas Ed25519 para interacciones de Discord.

## 📋 Requisitos

- **AWS CLI** y **AWS SAM CLI** instalados y configurados.
- **Python 3.12+**
- Cuenta de Discord con permisos de desarrollador.
- Token de Bot de Discord y Public Key.

## 🚀 Despliegue (AWS SAM)

Este proyecto utiliza AWS SAM (Serverless Application Model) para el despliegue.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/bicheon4ever.git
cd bicheon4ever
```

### 2. Configurar Credenciales

Necesitarás tu `DISCORD_TOKEN` y `DISCORD_PUBLIC_KEY` del Portal de Desarrolladores de Discord.

### 3. Construir y Desplegar

```bash
sam build
sam deploy --guided
```

Durante el despliegue guiado, se te pedirán los valores para:
- `DiscordToken`: Tu token de bot.
- `DiscordPublicKey`: Tu clave pública de aplicación.

Esto creará automáticamente:
- 2 Funciones Lambda (`InteractionsFunction`, `ScraperFunction`).
- 1 API Gateway (HTTP API).
- 2 Tablas DynamoDB (`BicheonConfig`, `BicheonState`).
- Reglas de EventBridge para el cron job.

### 4. Configurar URL de Interacciones en Discord

1. Copia la `InteractionsApiUrl` que aparece al final del despliegue de SAM.
2. Ve al [Discord Developer Portal](https://discord.com/developers/applications).
3. En tu aplicación, ve a **General Information**.
4. Pega la URL en el campo **Interactions Endpoint URL**.
5. Guarda los cambios.

## 💻 Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/usar [canal]` | Configura el canal donde se publicarán las noticias automáticas. |
| `/estado-bot` | Muestra el estado del bot y la última vez que se detectó contenido nuevo por categoría. |
| `/verificar-parche` | Busca manualmente el último Patch Note y muestra un resumen. |
| `/verificar-evento` | Busca manualmente el último Evento y muestra un resumen. |
| `/verificar-noticia` | Busca manualmente la última Noticia y muestra un resumen. |

## 📁 Estructura del Proyecto

```
bicheon4ever/
├── template.yaml              # Plantilla AWS SAM (Infraestructura como Código)
├── lambda_function.py         # Handlers de Lambda (Interacciones y Worker)
├── core_logic.py              # Lógica de negocio (Scraping, Formateo, Traducción)
├── database.py                # Adaptador para DynamoDB
├── requirements.txt           # Dependencias Python
└── README.md                  # Esta documentación
```

## 🔧 Desarrollo Local

Puedes probar las funciones localmente usando SAM:

```bash
sam local invoke InteractionsFunction -e events/interaction_example.json
```

## 📝 Licencia

GNU General Public License v3.0 - Ver archivo `LICENSE`

---

**Hecho con ❤️ para la comunidad de MIR4** 🐉
