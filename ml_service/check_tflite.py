
import mediapipe as mp
import numpy as np
import os
from pathlib import Path

# Try to find the interpreter
try:
    import tflite_runtime.interpreter as tflite
    print("Found tflite_runtime")
except ImportError:
    try:
        import tensorflow as tf
        print("Found tensorflow")
    except ImportError:
        print("Neither tflite_runtime nor tensorflow found")

try:
    # Mediapipe's internal tflite
    from mediapipe.python._framework_bindings import resource_util
    print("Mediapipe resource_util available")
except ImportError:
    print("Mediapipe resource_util NOT available")

# Check if we can use mediapipe's own runtime
try:
    # Some versions of mediapipe hide it here
    from mediapipe.tasks.python.core.base_options import BaseOptions
    print("Mediapipe tasks available")
except ImportError:
    print("Mediapipe tasks NOT available")
