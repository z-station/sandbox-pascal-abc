# Тесты запускать только в контейнере!
import pytest
import subprocess
from unittest.mock import call
from app.service.main import PascalService
from app import config, messages
from app.entities import (
    DebugData,
    TestsData,
    TestData
)
from app.service.entities import ExecuteResult
from app.service.entities import PascalFile
from app.service.exceptions import CheckerException
from app.service import exceptions


def test_execute__float_result__ok():

    """ Задача "Дробная часть" """

    # arrange
    data_in = '9.08'
    code = (
        'var a: double\n;'
        'i: double;\n'
        'begin\n'
        'readln (a);\n'
        'i := a - round(a);\n'
        'writeln(i)\n'
        'end.'
    )
    file = PascalFile(code)
    PascalService._compile(file)

    # act
    exec_result = PascalService._execute(
        data_in=data_in,
        file=file
    )

    # assert
    assert round(float(exec_result.result), 2) == 0.08
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_integer__ok():

    """ Задача "Делёж яблок" """

    # arrange
    data_in = (
        '6\n'
        '50'
    )
    code = (
        'program apples;\n'
        'var n,k: integer;\n'
        'begin\n'
        'readln(n,k);\n'
        'writeln(k div n);\n'
        'write(k mod n)\n'
        'end.'
    )
    file = PascalFile(code)
    PascalService._compile(file)

    # act
    exec_result = PascalService._execute(
        file=file,
        data_in=data_in
    )

    # assert
    assert exec_result.result == (
        '8\n'
        '2'
    )
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_string__ok():

    """ Задача "Замена подстроки" """

    # arrange
    data_in = '1213141516171819101'
    code = (
        'var s,new_s: string;\n'
        'i: integer;\n'
        'begin\n'
        'readln(s);\n'
        'new_s:=\'\';\n'
        'for i:=1 to length(s) do\n'
        'begin\n'
        'if s[i]= \'1\' then\n'
        'new_s:=new_s+\'one\'\n'
        'else\n'
        'new_s:=new_s+s[i];\n'
        'end;\n'
        'write(new_s);\n'
        'end.'
    )
    file = PascalFile(code)
    PascalService._compile(file)

    # act
    exec_result = PascalService._execute(
        data_in=data_in,
        file=file
    )

    # assert
    assert exec_result.result == 'one2one3one4one5one6one7one8one9one0one'
    assert exec_result.error is None
    file.remove()


def test_execute__empty_result__return_none():

    # arrange
    code = 'begin\nend.'
    file = PascalFile(code)
    PascalService._compile(file)

    # act
    exec_result = PascalService._execute(
        file=file
    )

    # assert
    assert exec_result.result is None
    assert exec_result.error is None
    file.remove()


def test_execute__timeout__return_error(mocker):

    # arrange
    code = (
        'var c: integer;\n'
        'begin\n'
        'c:=0;\n'
        'while c = 0 do\n'
        'writeln(\'UWU\');\n'
        'end.'
    )
    file = PascalFile(code)
    PascalService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = PascalService._execute(file=file)

    # assert
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__deep_recursive__error(mocker):

    """ Числа Фибоначчи """

    # arrange
    code = (
        'function fib(i:integer): longint;\n'
        'begin\n'
        'if i<=2 then\n'
        'fib:=1\n'
        'else\n'
        'fib:=fib(i-1)+fib(i-2)\n'
        'end;\n'
        'begin\n'
        'var n : integer;\n'
        'readln(n);\n'
        'writeln(fib(n));\n'
        'end.'
    )
    file = PascalFile(code)
    PascalService._compile(file)
    mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = PascalService._execute(file=file, data_in='50')

    # assert
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__write_access__error():

    """ Тест работает только в контейнере
        т.к. там ограничены права на запись в файловую систему """

    # arrange
    code = (
        'var f:text;\n'
        'begin\n'
        'assign(f,\'/app/src/file.txt\');\n'
        'rewrite(f);\n'
        'for var i := 1 to 5 do\n'
        'writeln(f,\'text\');\n'
        'close(f);\n'
        'end.'
    )
    file = PascalFile(code)
    PascalService._compile(file)

    # act
    exec_result = PascalService._execute(file=file)

    # assert
    assert exec_result.error == (
        'Access to the path \"/app/src/file.txt\" is denied.'
    )
    assert exec_result.result is None
    file.remove()


def test_execute__proc_exception__return_error(mocker):

    # arrange
    code = 'Some code'
    data_in = 'Some data in'
    error_msg = 'some error'
    file = PascalFile(code)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception(error_msg)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    result = PascalService._execute(file=file, data_in=data_in)

    # assert
    communicate_mock.assert_called_once_with(
        input=data_in,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    file.remove()
    assert result.error == error_msg
    assert result.result is None


def test_compile__timeout__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=subprocess.TimeoutExpired(cmd='', timeout=config.TIMEOUT)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = PascalService._compile(file_mock)

    # assert
    assert error == messages.MSG_1
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__exception__return_error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    error_msg = 'some error'
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)

    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception(error_msg)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    result = PascalService._compile(file_mock)

    # assert
    assert result == error_msg
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__error__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, compile_error)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = PascalService._compile(file_mock)

    # assert
    assert error == compile_error
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)
    mocker.patch.object(subprocess.Popen, '__init__', return_value=None)
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, None)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    PascalService._compile(file_mock)

    # assert
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_check__true__ok():

    # arrange
    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    check_result = PascalService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is True


def test_check__false__ok():

    # arrange
    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    check_result = PascalService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is False


def test_check__invalid_checker_func__raise_exception():

    # arrange
    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        PascalService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_2


def test_check__checker_func_no_return_instruction__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  result = right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        PascalService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_3


def test_check__checker_func_return_not_bool__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return None'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        PascalService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_4


def test_check__checker_func__invalid_syntax__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  include(invalid syntax here)'
        '  return True'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        PascalService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_5
    assert ex.value.details == 'invalid syntax (<string>, line 1)'


def test_debug__compile_is_success__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.PascalService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.PascalService._execute',
        return_value=execute_result
    )
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = PascalService.debug(data)

    # assert
    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_called_once_with(
        file=file_mock,
        data_in=data.data_in
    )
    assert debug_result.result == execute_result.result
    assert debug_result.error == execute_result.error


def test_debug__compile_return_error__ok(mocker):

    # arrange
    compile_error = 'some error'
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.PascalService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.PascalService._execute')
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = PascalService.debug(data)

    # assert
    file_mock.remove.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    assert debug_result.result is None
    assert debug_result.error == compile_error


def test_testing__compile_is_success__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)
    compile_mock = mocker.patch(
        'app.service.main.PascalService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.PascalService._execute',
        return_value=execute_result
    )
    check_result = mocker.Mock()
    check_mock = mocker.patch(
        'app.service.main.PascalService._check',
        return_value=check_result
    )
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = PascalService.testing(data)

    # assert
    compile_mock.assert_called_once_with(file_mock)
    assert execute_mock.call_args_list == [
        call(
            file=file_mock,
            data_in=test_1.data_in
        ),
        call(
            file=file_mock,
            data_in=test_2.data_in
        )
    ]
    assert check_mock.call_args_list == [
        call(
            checker_func=data.checker,
            right_value=test_1.data_out,
            value=execute_result.result
        ),
        call(
            checker_func=data.checker,
            right_value=test_2.data_out,
            value=execute_result.result
        )
    ]
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.result
    assert tests_result[0].error == execute_result.error
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.result
    assert tests_result[1].error == execute_result.error
    assert tests_result[1].ok == check_result


def test_testing__compile_return_error__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    file_mock.remove = mocker.Mock()
    mocker.patch.object(PascalFile, '__new__', return_value=file_mock)
    compile_error = 'some error'
    compile_mock = mocker.patch(
        'app.service.main.PascalService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.PascalService._execute')
    check_mock = mocker.patch('app.service.main.PascalService._check')
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )

    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = PascalService.testing(data)

    # assert
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    check_mock.assert_not_called()
    file_mock.remove.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result is None
    assert tests_result[0].error == compile_error
    assert tests_result[0].ok is False
    assert tests_result[1].result is None
    assert tests_result[1].error == compile_error
    assert tests_result[1].ok is False
