import PIL.PngImagePlugin
from sorl.thumbnail.engines.pil_engine import Engine as PilEngine


# Increase the PMG size limit for thumbnails
_SAFE_TEXT_CHUNK = 10485760 # 10MB

class SafePilEngine(PilEngine):
    def get_image(self, source):
        original = PIL.PngImagePlugin.MAX_TEXT_CHUNK
        PIL.PngImagePlugin.MAX_TEXT_CHUNK = _SAFE_TEXT_CHUNK
        try:
            return super().get_image(source)
        finally:
            PIL.PngImagePlugin.MAX_TEXT_CHUNK = original
