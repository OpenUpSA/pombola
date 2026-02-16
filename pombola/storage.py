from pipeline.storage import PipelineMixin
from whitenoise.storage import CompressedStaticFilesStorage


class PipelineCompressedStaticFilesStorage(PipelineMixin, CompressedStaticFilesStorage):
    pass
