from enum import Enum


class CourseTypes(Enum):
    ECHAUFFEMENT = 'echauffement'
    ENTRAINEMENT = 'entrainement'
    EVALUATION = 'evaluation'
    AUTRE = 'autre'


class ModuleTypes(Enum):
    FICHIER = 'fichier'
    FORUM = 'forum'
    FORUM_AVANCE = 'forum_avance'
    PAGE = 'page'
    TEST = 'test'
    VIDEO = 'video'
    DEVOIR = 'devoir'
    AUTRE = 'autre'


class ContentTypes(Enum):
    RECETTE = 'recette'
    INTRODUCTION = 'introduction'
    QUIZ = 'quiz'


class QuestionTypes(Enum):
    SELECT = 'select'
    CHECKBOX = 'checkbox'
    RADIO = 'radio'
    CONTROL_GROUP = 'control_group'