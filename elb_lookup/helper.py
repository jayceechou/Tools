from typing import List
import pprint
import json
import re

def go_pprint(py_obj:object, depth:int) -> str:
    pp = pprint.PrettyPrinter(indent=depth)
    pp.pprint(py_obj)


def go_validate_ipv4(octects:List) -> bool:
    if len(octects) != 4:
        return False
    for oct in octects:
        if not oct.isdigit() or int(oct) > 255 or int(oct) < 0:
            return False
    return True    


def get_ipv4(text) -> List[str]:
    if not text:
        return []
    
    pattern = re.compile(r'((\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}))')
    ipv4 = []
    for match in pattern.findall(repr(text)):
        if go_validate_ipv4(match[1:]) and match[0] not in ipv4:
            ipv4.append(match[0])
    return ipv4


def load_json(filename:str) -> dict:
    if not filename:
        print("No valid file name.")
        return {}
    
    with open(filename, 'r') as f:
        py_obj = json.load(f)

    return py_obj


def save_json(py_obj:object, filename:str) -> bool:
    if not py_obj:
        return False
    elif not filename:
        print("No valid file name.")
        return False    
    
    with open(filename, 'w') as f:
        json.dump(py_obj, f, indent=2)
    return True