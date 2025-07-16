from enum import Enum

class StepType(Enum):
    TEXT = "text"
    VIDEO = "video"
    QUIZ = "quiz"
    DOCUMENT = "document"
    IFRAME = "iframe"
    # Add other step types as needed 