
import langfuse
import pprint

print(f"Langfuse file: {langfuse.__file__}")
print("Langfuse attributes:")
pprint.pprint(dir(langfuse))

try:
    import langfuse.decorators
    print("Successfully imported langfuse.decorators")
except  ImportError as e:
    print(f"Failed to import langfuse.decorators directly: {e}")

try:
    from langfuse import decorators
    print("Successfully imported decorators from langfuse")
except ImportError as e:
    print(f"Failed to import decorators from langfuse: {e}")
