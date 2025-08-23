# Project Agent Fantasy

---
This project make to show that Agent can be control discord bot with properly tool and system prompt.

## Features
- Unlimit Extension (Using MCP SSE to extend the bot tool)
- Dynamicly Module
- Easy to use and manage

## Installation & Deployment

###  Native
- Clone the repository
- Install the required packages
```bash
pip install -r requirements.txt
```
- Copy the Environment file
```bash
cp .env.example .env
```
- Edit the Environment file
- Run the bot
```bash
python main.py
```

### Docker

- Clone the repository
- Build the docker image
```bash
docker build -t ai-fantasy .
```
- Run the docker image*
```bash
docker run -d --name ai-fantasy ai-fantasy
```

\* Note: If use docker please make sure to set the environment variable in the docker run command or in docker compose file.

## Acknowledgments

Special thanks to [Dương Lê Giang](https://www.facebook.com/share/1G2qdcFfBC/) for providing invaluable guidance on RAG (Retrieval-Augmented Generation) concepts that formed the foundation of this implementation.

## Project Structure
- `modules` - This folder contains all tool built-in for bot functions.
- `objs` - This folder contains all typing objects for tool args ( tool decorator auto turn function args to json schema).
- `classs` - This folder contains all class for bot functions.
- `resources` - This folder contains system prompt and other resources.