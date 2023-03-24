import logging
import os.path
import subprocess
import tempfile

import api.base
from service.tool import audio_normalize

logger = logging.getLogger(__name__)


# noinspection PyAbstractClass
class AudioNormalizerHandler(api.base.ApiHandler):
    async def post(self):
        try:
            import uuid
            uploaded_file = self.request.files['srcaudio'][0]
            file_data = uploaded_file['body']
            full_filename = uploaded_file['filename']

            output_filename = await audio_normalize(full_filename=full_filename, file_data=file_data)

            if not output_filename:
                raise SystemError()

            with open(output_filename, 'rb') as f:
                self.set_header('Content-Type', 'audio/wav')
                self.set_header('Content-Disposition', 'attachment; filename="converted_audio.wav"')
                self.write(f.read())
                await self.flush()
                os.remove(output_filename)
        except Exception as e:
            logger.exception(e)
            self.set_status(500)
            self.write({
                "code": 500,
                "msg": "system_error",
                "data": None
            })
