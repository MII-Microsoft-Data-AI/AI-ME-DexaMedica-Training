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

# --- Your Singleton Class ---
@singleton
class AClass:
    """
    This is your class 'AClass' that is now a singleton.
    You can only ever have one object of this class in your program.
    """
    def __init__(self, value=100):
        # The constructor will only be called the very first time an instance is created.
        self.a_value = value
        print(f"AClass instance created with value: {self.a_value}")

    def get_A(self):
        """
        A method to return the value of the 'a_value' attribute.
        """
        return self.a_value

# --- Example Usage & Verification ---

print("--- Testing the AClass Singleton ---")

# Create the first instance. The __init__ method is called.
a1 = AClass(value=50)

# Call the method to get its value.
print(f"Value from a1: {a1.get_A()}")

# Try to create a second instance with a different value.
# The __init__ method will NOT be called again, and the original instance is returned.
a2 = AClass(value=200)

# The returned object is the same, so its value is also the same.
print(f"Value from a2: {a2.get_A()}")

# Check if both variables refer to the exact same object in memory.
print(f"Are a1 and a2 the same object? {a1 is a2}")
