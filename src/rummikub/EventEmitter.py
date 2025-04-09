class EventEmitter:
    """
    A simple event emitter for Python inspired by Node.js EventEmitter
    Allows components to communicate without direct dependencies
    """
    
    def __init__(self):
        self._events = {}
        
    def on(self, event, callback):
        """Register an event handler"""
        if event not in self._events:
            self._events[event] = []
        self._events[event].append(callback)
        return self
        
    def once(self, event, callback):
        """Register an event handler that will be called at most once"""
        def one_time_callback(*args, **kwargs):
            self.off(event, one_time_callback)
            callback(*args, **kwargs)
        
        return self.on(event, one_time_callback)
        
    def emit(self, event, *args, **kwargs):
        """Emit an event with arguments"""
        if event in self._events:
            for callback in self._events[event]:
                callback(*args, **kwargs)
        return self
        
    def off(self, event, callback=None):
        """Remove an event handler or all handlers for an event"""
        if event in self._events:
            if callback:
                self._events[event] = [cb for cb in self._events[event] if cb != callback]
            else:
                self._events[event] = []
        return self
        
    def listeners(self, event):
        """Get all listeners for an event"""
        return self._events.get(event, [])
        
    def event_names(self):
        """Get all registered event names"""
        return list(self._events.keys())

# Create a singleton instance
event_emitter = EventEmitter()