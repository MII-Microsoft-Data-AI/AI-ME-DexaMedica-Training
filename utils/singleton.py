import functools

# --- The Decorator Pattern for Singleton ---
# This is a general-purpose and very "Pythonic" way to make a class a singleton.

def singleton(cls):
    """
    A decorator to make a class a Singleton.
    It ensures that only one instance of the decorated class can exist.
    """
    # This dictionary will store the single instance of the class.
    instances = {}

    # The wrapper function acts as the new constructor for the decorated class.
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        # Check if an instance of the class already exists.
        if cls not in instances:
            # If not, create a new instance and store it.
            instances[cls] = cls(*args, **kwargs)
        # Always return the same, stored instance.
        return instances[cls]
    
    return wrapper