# Slay the Spire AI

An AI-powered bot that plays Slay the Spire using OpenAI's GPT-4 or Anthropic's Claude. The bot reads the game state and makes intelligent decisions about card plays, pathing, and other in-game choices.

## Requirements

- Python 3.8+
- Slay the Spire with Communication Mod installed
- API keys for either:
  - OpenAI GPT-4 (set as `OPENAI_API_KEY` environment variable)
  - Anthropic Claude (set as `CLAUDE_API_KEY` environment variable)

## Setup

1. Install Python dependencies:
```bash
pip install anthropic openai tkinter
```

2. Install the Communication Mod for Slay the Spire:
   - Subscribe to [Communication Mod on Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=2131373661)
   - Enable the mod in-game

3. Set up your API keys as environment variables:
```bash
# For OpenAI GPT-4
export OPENAI_API_KEY='your-api-key'

# For Anthropic Claude
export CLAUDE_API_KEY='your-api-key'
```

## Usage

1. Start Slay the Spire with Communication Mod enabled
2. Run the bot:
```bash
python main.py
```
3. The UI will appear showing the game state and AI's decisions
4. Use the controls to:
   - Start/Stop AI decision making
   - Toggle automatic action execution
   - View debug information
   - Monitor the AI's thought process

## Features

- Reads complete game state including:
  - Cards in hand/deck/discard
  - Enemy intents and status effects
  - Player health, energy, and status effects
  - Relics and potions
- Makes intelligent decisions about:
  - Combat strategies
  - Path choices
  - Card rewards
  - Shop purchases
  - Events and rest sites
- Real-time UI showing game state and AI reasoning
- Support for both GPT-4 and Claude AI models
- Automatic action execution
- Debug logging

## Files

- `main.py` - Main program and UI
- `gamestatetooutput.py` - Game state parsing and AI integration
- `data/` - JSON files containing game data
  - Card descriptions
  - Relic effects
  - Potion effects
  - Power/status effect descriptions

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT License
