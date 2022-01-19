import traceback
from pipeline.compressors.yui import YUICompressor

class LoggingYUICompressor(YUICompressor):
  def compress_js(self, js):
      try:
          return super(LoggingYUICompressor, self).compress_js(js)
      except Exception, e:
          print("Error in the following content (this might be a bundle and not a source file):\n")
          print(js)
          raise e

  def compress_css(self, css):
      try:
          return super(LoggingYUICompressor, self).compress_css(css)
      except Exception, e:
          print("Error in the following content (this might be a bundle and not a source file):\n")
          print(css)
          raise e
