import random
import time
import math
from typing import Any, Dict, List, Optional, Callable

# Module level state
_next_id = 0
_seed = 0
_base_delta = 1000 / 60  # ~16.666ms for 60fps
_warn_once_history = {}


def extend(base: Dict, *args, deep: bool = False) -> Dict:
    for obj in args:
        if obj is None:
            continue
        for key, value in obj.items():
            if deep and isinstance(value, dict) and isinstance(base.get(key), dict):
                extend(base[key], value, deep=True)
            else:
                base[key] = value
    return base


def clone(obj: Any, deep: bool = False) -> Any:
    if obj is None:
        return None
    
    if isinstance(obj, dict):
        if deep:
            result = {}
            for key, value in obj.items():
                result[key] = clone(value, deep=True)
            return result
        return dict(obj)
    
    if isinstance(obj, list):
        if deep:
            return [clone(item, deep=True) for item in obj]
        return list(obj)
    
    return obj


def next_id() -> int:
    global _next_id
    _next_id += 1
    return _next_id


def reset_id() -> None:
    global _next_id
    _next_id = 0


def random_float(min_val: float = 0, max_val: float = 1) -> float:
    return min_val + random.random() * (max_val - min_val)


def random_int(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def random_choice(choices: List[Any]) -> Any:
    return random.choice(choices)


def choose(choices: List[Any]) -> Any:
    return random_choice(choices)


def is_element(obj: Any) -> bool:
    return False


def is_array(obj: Any) -> bool:
    return isinstance(obj, list)


def is_function(obj: Any) -> bool:
    return callable(obj)


def is_plain_object(obj: Any) -> bool:
    return isinstance(obj, dict)


def is_string(obj: Any) -> bool:
    return isinstance(obj, str)


def clamp(value: float, min_val: float, max_val: float) -> float:
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def sign(value: float) -> int:
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def now() -> float:
    return time.time() * 1000


def shuffle(array: List[Any]) -> List[Any]:
    random.shuffle(array)
    return array


def keys(obj: Dict) -> List[str]:
    return list(obj.keys())


def values(obj: Dict) -> List[Any]:
    return list(obj.values())


def index_of(array: List[Any], value: Any) -> int:
    try:
        return array.index(value)
    except ValueError:
        return -1


def map_list(array: List[Any], func: Callable) -> List[Any]:
    return list(map(func, array))


def chain_func(funcs: List[Callable]) -> Callable:
    def chained(*args, **kwargs):
        result = None
        for func in funcs:
            result = func(*args, **kwargs)
        return result
    return chained


def get(obj: Dict, path: str, default: Any = None) -> Any:
    keys = path.split('.')
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def set_value(obj: Dict, path: str, value: Any) -> None:
    keys = path.split('.')
    current = obj
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def info_string(obj: Any) -> str:
    return str(obj)


def color_to_number(color: str) -> int:
    if color.startswith('#'):
        color = color[1:]
    return int(color, 16)


def log(*args) -> None:
    print(*args)


def warn(*args) -> None:
    print('Warning:', *args)


def warn_once(key: str, *args) -> None:
    global _warn_once_history
    if key not in _warn_once_history:
        _warn_once_history[key] = True
        warn(*args)


def deprecated(obj: Any, prop: str, warning: str) -> None:
    pass


def normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle <= -math.pi:
        angle += 2 * math.pi
    return angle
