
import sys
import os
sys.path.append(os.getcwd())

from strands import Agent
import inspect

print("Inspecting strands.Agent:")
print(inspect.getsource(Agent))
