"""
Doesn't actually do any processing, just provides a default model API from raspy.

model = Model(projectPath), then use that as model argument elsewhere - no direct interaction with raspy needed.
"""

from raspy import Ras, API

def Model(projectPath):
    return API(Ras(projectPath))