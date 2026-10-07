import os

# the local scene-planner model is minutes per scene; unit tests run the
# rule-based staging unless a test turns the planner on itself
os.environ.setdefault('NEXSTUDIO_SCENE_LLM', 'off')
