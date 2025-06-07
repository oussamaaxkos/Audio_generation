import elevenlabs
import inspect

# Print module
print("elevenlabs module:", elevenlabs)

# Print all attributes in elevenlabs
print("\nAvailable attributes in elevenlabs:")
for attr in dir(elevenlabs):
    if not attr.startswith('__'):
        print(f"- {attr}")

# Print the __init__ file content if we can
try:
    import os
    init_path = os.path.join(os.path.dirname(elevenlabs.__file__), "__init__.py")
    print(f"\nContents of {init_path}:")
    with open(init_path, 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Could not read __init__.py: {e}")