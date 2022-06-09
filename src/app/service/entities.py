import os
import uuid
from collections import namedtuple
from app import config

ExecuteResult = namedtuple('ExecuteResult', ('result', 'error'))


def opener(path, flags):
    return os.open(path, flags, mode=0o777)


class PascalFile:

    """ Описывает файлы, необходимые для запуска программы """

    def __init__(self, code: str):
        file_id = uuid.uuid4()
        self.filepath_pas = os.path.join(
            config.SANDBOX_DIR, f'{file_id}.pas'
        )
        self.filepath_exe = os.path.join(
            config.SANDBOX_DIR, f'{file_id}.exe'
        )
        with open(self.filepath_pas, 'w') as file:
            file.write(code)
        # with open(self.filepath_exe, 'w', opener=opener) as _:
        #     pass

    def remove(self):
        try:
            os.remove(self.filepath_pas)
            os.remove(self.filepath_exe)
        except:
            pass
