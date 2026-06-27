# Hermes TTS — Xiaomi MiMo

Hermes Agent plugin provider for Xiaomi MiMo-V2.5 TTS.

## Install

```bash
cd ~/github/hermes-tts-xiaomi-mimo
pip install -e .
```

## Configure

```yaml
tts:
  provider: xiaomi-mimo
  xiaomi-mimo:
    api_key: "${MIMO_API_KEY}"
    base_url: "https://api.xiaomimimo.com/v1"
    model: "mimo-v2.5-tts"
    voice: "冰糖"
```

## Notes
- First release is TTS-only.
- API key is read from `MIMO_API_KEY` only.
- Streaming is not implemented yet.
