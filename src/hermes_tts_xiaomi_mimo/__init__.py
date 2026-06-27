"""Hermes plugin entry for Xiaomi MiMo."""
from hermes_tts_xiaomi_mimo.provider import XiaomiMimoTTSProvider

def register(ctx):
    ctx.register_tts_provider(XiaomiMimoTTSProvider())
