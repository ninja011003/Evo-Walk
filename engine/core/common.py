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
    """
    Extends the base dict with properties from other dicts.
    If deep is True, performs a deep copy/merge.
    """
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
    """Clones an object (shallow or deep)."""
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
    """Returns the next unique sequential ID."""
    global _next_id
    _next_id += 1
    return _next_id


def reset_id() -> None:
    """Resets the ID counter to 0."""
    global _next_id
    _next_id = 0


def random_float(min_val: float = 0, max_val: float = 1) -> float:
    """Returns a random value between min and max."""
    return min_val + random.random() * (max_val - min_val)


def random_int(min_val: int, max_val: int) -> int:
    """Returns a random integer between min and max inclusive."""
    return random.randint(min_val, max_val)


def random_choice(choices: List[Any]) -> Any:
    """Returns a random item from the list."""
    return random.choice(choices)


def choose(choices: List[Any]) -> Any:
    """Alias for random_choice."""
    return random_choice(choices)


def is_element(obj: Any) -> bool:
    """Returns True if obj is a DOM element (always False in Python)."""
    return False


def is_array(obj: Any) -> bool:
    """Returns True if obj is a list."""
    return isinstance(obj, list)


def is_function(obj: Any) -> bool:
    """Returns True if obj is callable."""
    return callable(obj)


def is_plain_object(obj: Any) -> bool:
    """Returns True if obj is a plain dict."""
    return isinstance(obj, dict)


def is_string(obj: Any) -> bool:
    """Returns True if obj is a string."""
    return isinstance(obj, str)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamps a value to be within the specified range."""
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def sign(value: float) -> int:
    """Returns the sign of a value (-1, 0, or 1)."""
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def now() -> float:
    """Returns the current timestamp in milliseconds."""
    return time.time() * 1000


def shuffle(array: List[Any]) -> List[Any]:
    """Randomly shuffles the array in-place and returns it."""
    random.shuffle(array)
    return array


def keys(obj: Dict) -> List[str]:
    """Returns the keys of the dict as a list."""
    return list(obj.keys())


def values(obj: Dict) -> List[Any]:
    """Returns the values of the dict as a list."""
    return list(obj.values())


def index_of(array: List[Any], value: Any) -> int:
    """Returns the index of value in array, or -1 if not found."""
    try:
        return array.index(value)
    except ValueError:
        return -1


def map_list(array: List[Any], func: Callable) -> List[Any]:
    """Maps a function over the array."""
    return list(map(func, array))


def chain_func(funcs: List[Callable]) -> Callable:
    """Creates a function that chains multiple functions."""
    def chained(*args, **kwargs):
        result = None
        for func in funcs:
            result = func(*args, **kwargs)
        return result
    return chained


def get(obj: Dict, path: str, default: Any = None) -> Any:
    """Gets a value from a nested dict using a dot-separated path."""
    keys = path.split('.')
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def set_value(obj: Dict, path: str, value: Any) -> None:
    """Sets a value in a nested dict using a dot-separated path."""
    keys = path.split('.')
    current = obj
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def info_string(obj: Any) -> str:
    """Returns a string representation useful for debugging."""
    return str(obj)


def color_to_number(color: str) -> int:
    """Converts a hex color string to a number."""
    if color.startswith('#'):
        color = color[1:]
    return int(color, 16)


def log(*args) -> None:
    """Logs a message to the console."""
    print(*args)


def warn(*args) -> None:
    """Logs a warning message."""
    print('Warning:', *args)


def warn_once(key: str, *args) -> None:
    """Logs a warning message only once per key."""
    global _warn_once_history
    if key not in _warn_once_history:
        _warn_once_history[key] = True
        warn(*args)


def deprecated(obj: Any, prop: str, warning: str) -> None:
    """Marks a property as deprecated (no-op in Python)."""
    pass


def normalize_angle(angle: float) -> float:
    """Normalizes an angle to be within -pi to pi."""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle <= -math.pi:
        angle += 2 * math.pi
    return angle
