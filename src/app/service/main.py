import os
import subprocess
from typing import Optional
from app.service.entities import PascalFile
from app.entities import (
    DebugData,
    TestsData,

)
from app import config, messages
from app.service import exceptions
from app.service.entities import ExecuteResult
from app.utils import clean_str, clean_error


class PascalService:

    @classmethod
    def _preexec_fn(cls):
        def change_process_user():
            os.setgid(config.SANDBOX_USER_UID)
            os.setuid(config.SANDBOX_USER_UID)
        return change_process_user()

    @classmethod
    def _compile(cls, file: PascalFile) -> Optional[str]:

        """ Компилирует код программы """

        result, error = None, None
        pascal_path = '/usr/bin/pascal/pabcnetcclear.exe'
        proc = subprocess.Popen(
            args=['mono', pascal_path, file.filepath_pas],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            result, error = proc.communicate(timeout=config.TIMEOUT)
        except subprocess.TimeoutExpired:
            error = messages.MSG_1
        except Exception as ex:
            error = str(ex)
        finally:
            proc.kill()
        if result and result != 'OK\n':
            error = result
        return clean_error(error)

    @classmethod
    def _execute(
        cls,
        file: PascalFile,
        data_in: Optional[str] = None
    ) -> ExecuteResult:

        """ Запускает скомпилирвованный файл,
            передает входные данные
            и возвращает результат работы программы """

        proc = subprocess.Popen(
            args=['mono', file.filepath_exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=cls._preexec_fn,
            text=True
        )
        try:
            result, error = proc.communicate(
                input=data_in,
                timeout=config.TIMEOUT
            )
        except subprocess.TimeoutExpired:
            result, error = None, messages.MSG_1
        except Exception as ex:
            result, error = None, str(ex)
        finally:
            proc.kill()
        if result == '\uffff':
            result = None
            error = messages.MSG_8
        return ExecuteResult(
            result=clean_str(result or None),
            error=clean_error(error or None)
        )

    @classmethod
    def _validate_checker_func(cls, checker_func: str):
        if not checker_func.startswith(
            'def checker(right_value: str, value: str) -> bool:'
        ):
            raise exceptions.CheckerException(messages.MSG_2)
        if checker_func.find('return') < 0:
            raise exceptions.CheckerException(messages.MSG_3)

    @classmethod
    def _check(cls, checker_func: str, **checker_func_vars) -> bool:
        cls._validate_checker_func(checker_func)
        try:
            exec(
                checker_func + '\nresult = checker(right_value, value)',
                globals(),
                checker_func_vars
            )
        except Exception as ex:
            raise exceptions.CheckerException(
                message=messages.MSG_5,
                details=str(ex)
            )
        else:
            result = checker_func_vars['result']
            if not isinstance(result, bool):
                raise exceptions.CheckerException(messages.MSG_4)
            return result

    @classmethod
    def debug(cls, data: DebugData) -> DebugData:
        file = PascalFile(data.code)
        error = cls._compile(file)
        if error:
            data.error = error
        else:
            exec_result = cls._execute(
                file=file,
                data_in=data.data_in
            )
            data.result = exec_result.result
            data.error = exec_result.error
        file.remove()
        return data

    @classmethod
    def testing(cls, data: TestsData) -> TestsData:
        file = PascalFile(data.code)
        error = cls._compile(file)
        for test in data.tests:
            if error:
                test.error = error
                test.ok = False
            else:
                exec_result = cls._execute(
                    file=file,
                    data_in=test.data_in
                )
                test.result = exec_result.result
                test.error = exec_result.error
                test.ok = cls._check(
                    checker_func=data.checker,
                    right_value=test.data_out,
                    value=test.result
                )
        file.remove()
        return data
