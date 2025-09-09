import re
from typing import Optional
from app import messages


def clean_str(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        value = value.replace('\ufeff', '')
        if not value:
            return None
        return value.replace('\r', '').rstrip('\n')
    return value


def clean_error(value: Optional[str]) -> Optional[str]:
    if isinstance(value, str):
        value = value.replace('\ufeff', '')
        if not value:
            return None
        value = re.sub(
            pattern='(\S)*.pas',
            repl="main.pas",
            string=value
        )
        if 'Terminated' in value:
            value = messages.MSG_1
        elif 'Попытка считывания за концом потока ввода' in value:
            value = messages.MSG_8
        else:
            result = re.findall(
                pattern='Access to the path ".+" is denied.',
                string=value
            )
            if result:
                value = result[0]
    return value
