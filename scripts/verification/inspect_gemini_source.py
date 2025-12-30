
import sys
import os
sys.path.append(os.getcwd())

import strands.models.gemini as gemini_module
import inspect

print("Inspecting strands.models.gemini:")
print(inspect.getsource(gemini_module))
