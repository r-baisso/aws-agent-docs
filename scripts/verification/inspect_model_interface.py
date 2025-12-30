
import sys
import os
sys.path.append(os.getcwd())

from strands.models import Model
import inspect

print("Inspecting strands.models.Model:")
print(inspect.getsource(Model))
