from typing import Dict, Any, List, Callable, Optional


def on(obj: Dict, event_names: str, callback: Callable) -> Callable:
    """
    Subscribes a callback function to the given object's event(s).
    Multiple event names can be provided separated by spaces.
    """
    names = event_names.split(' ')
    
    for name in names:
        if 'events' not in obj:
            obj['events'] = {}
        if name not in obj['events']:
            obj['events'][name] = []
        obj['events'][name].append(callback)
    
    return callback


def off(obj: Dict, event_names: str, callback: Callable) -> None:
    """
    Removes the given event callback.
    If no callback, clears all callbacks for that event.
    If no event, clears all events on the object.
    """
    if 'events' not in obj:
        return
    
    if not event_names:
        obj['events'] = {}
        return
    
    names = event_names.split(' ')
    
    for name in names:
        callbacks = obj['events'].get(name, [])
        
        if callback:
            try:
                callbacks.remove(callback)
            except ValueError:
                pass
        else:
            obj['events'][name] = []


def trigger(obj: Dict, event_names: str, event: Optional[Dict] = None) -> None:
    """
    Fires all the callbacks subscribed to the given object's event(s).
    """
    if 'events' not in obj:
        return
    
    names = event_names.split(' ')
    
    for name in names:
        callbacks = obj['events'].get(name, [])
        
        if callbacks:
            event_obj = event or {}
            event_obj['name'] = name
            event_obj['source'] = obj
            
            for callback in callbacks:
                callback(event_obj)
