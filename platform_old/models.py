from django.db import models
from .enums import CourseTypes, ModuleTypes, ContentTypes
import re


class Course(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    external_id = models.IntegerField(null=False)
    title = models.CharField(max_length=500)
    type = models.CharField(max_length=200)
    link = models.URLField()

    def __str__(self):
        return self.title

    def get_course_type(self):
        if re.search('(.*)Echauffement(.*)', self.title):
            self.type = CourseTypes.ECHAUFFEMENT.value
            return self.type
        if re.search('(.*)Entraînement(.*)', self.title):
            self.type = CourseTypes.ENTRAINEMENT.value
        if re.search('(.*)Evaluation(.*)', self.title):
            self.type = CourseTypes.EVALUATION.value
            return self.type
        self.type = CourseTypes.AUTRE.value
        return self.type

    def get_external_id(self):
        matchs = re.search(r'(https://ichefpro.com/course/view.php\?id=)(\d+)', self.link)
        if matchs:
            self.external_id = matchs.group(2)
        return self.external_id

    def get_id(self):
        self.id = str(self.external_id)
        return self.id


class Module(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    external_id = models.IntegerField(null=False)
    course=models.ForeignKey(to=Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    type_extracted = models.CharField(max_length=200, null=True)
    type_cleaned = models.CharField(max_length=200, null=True)
    type = models.CharField(max_length=200)
    link = models.URLField()
    is_completed = models.BooleanField()
    html_module_index = models.IntegerField()

    def __str__(self):
        return self.title

    def get_external_id(self):
        matchs = re.search(r'(https://ichefpro.com/mod/.*/view.php\?id=)(\d+)', self.link)
        if matchs:
            self.external_id = matchs.group(2)
        return self.external_id

    def get_id(self):
        self.id = self.course.id + '-' + str(self.external_id)
        return self.id

    def get_module_type(self):
        for module_type in ModuleTypes:
            self.type_cleaned = self.type_extracted.replace(' ', '_').replace('é', 'e').lower()
            if self.type_cleaned == module_type.value:
                self.type = module_type.value
                return self.type
        self.type = ModuleTypes.AUTRE.value
        return self.type

    def get_is_completed(self, html_module):
        if self.type == ModuleTypes.FORUM_AVANCE.value:
            self.is_completed = True
            return self.is_completed
        try:
            if not html_module.find('span', class_="autocompletion"):
                self.is_completed = True
                return self.is_completed
            completed_text = html_module.find('span', class_="autocompletion").find('img')['title']
            if re.search('(Terminé )(.*)', completed_text):
                self.is_completed = True
                return self.is_completed
            self.is_completed = False
            return self.is_completed
        except:
            breakpoint()


class Content(models.Model):
    module = models.ForeignKey(
        to=Module,
        related_name='contents',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=500)
    type = models.CharField(max_length=200)
    internal_path = models.URLField(null=True)

    def __str__(self):
        return self.title

    def get_type(self):
        if self.module.type == ModuleTypes.VIDEO.value and re.search('(Recette)(.*)', self.title):
            self.type = ContentTypes.RECETTE.value
        if self.module.type == ModuleTypes.VIDEO.value and re.search('(.*)(Introduction)(.*)', self.title):
            self.type = ContentTypes.INTRODUCTION.value
        return self.type


class Quiz(models.Model):
    content = models.ForeignKey(to=Content, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    html_quiz = models.TextField()
    type = models.CharField(max_length=500)

    def __str__(self):
        return self.title

    def get_type(self):
        pass


class Question(models.Model):
    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE)
    text = models.TextField()
    type = models.CharField(max_length=200)
    html_question = models.TextField()

    def __str__(self):
        return self.text

    def get_type(self):
        pass


class Answer(models.Model):
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE)
    text = models.TextField()
    is_right_answer = models.BooleanField()
    html_answer = models.TextField()
    control_group_rank = models.IntegerField(null=True)
    html_control_group = models.TextField()

    def __str__(self):
        return self.text

    def get_is_right_answer(self):
        if self.question.text == "Associez les noms des recettes avec leur description : Cuisson à l'anglaise":
            return self.text == "préparations généralement cuites dans l'eau ou à la vapeur (légumes) ou dans un fond blanc (viandes et volailles)."
        if self.question.text == "Associez les noms des recettes avec leur description : Dubarry":
            return self.text == "recettes à base de chou-fleur"
        if self.question.text == "Associez les noms des recettes avec leur description : Bonne-femme":
            return self.text == "préparation évoquant une cuisine mijotée, simple et familiale souvent servie dans son ustensile de cuisson (marmite, casserole)."
        if self.question.text == "Associez les noms des recettes avec leur description : Melba":
            return self.text == "recette composée de pêche, de glace vanille et de coulis de fruits rouges"
        if self.question.text == "Associez les noms des recettes avec leur description : À la Dugléré":
            return self.text == "poché à court mouillement dans un fumet de poisson au vin blanc sur un lit de tomates concassées, d'oignons et échalotes ciselés et de persil haché"
        if self.question.text == "Associez les noms des recettes avec leur description : Marengo":
            return self.text == "préparation à base de veau ou de poulet, de tomates, d'ail et de vin blanc."
        if self.question.text == "Associez les noms des recettes avec leur description : Argenteuil":
            return self.text == "recettes à base d'asperges"
        if self.question.text == "Je suis le lien entre la salle et la cuisine, je suis":
            return re.search("(.*)(l'annonceur)(.*)", self.text)
        if self.question.text == "Comment appelle-t-on un dessous de plat dans un contexte professionnel ?":
            return re.search("(.*)(doublure)(.*)", self.text)
        if self.question.text == "L'escoffier est-il un plat ovale ?":
            return re.search("(.*)(Faux)(.*)", self.text)
        if self.question.text == "On ne recouvre jamais un plat de service !":
            return re.search("(.*)(Faux)(.*)", self.text)
        if self.question.text == "A quoi sert une duxelle de champignons ?":
            # All answers are right
            return True
        if self.question.text == "Remettre les étapes de réalisation de la duxelle de champignons dans le bon ordre :" and self.control_group_rank == 0:
            return self.text == "Nettoyer ou éplucher les champignons de Paris"
        if self.question.text == "Remettre les étapes de réalisation de la duxelle de champignons dans le bon ordre :" and self.control_group_rank == 1:
            return self.text == "Ciseler finement les échalotes"
        if self.question.text == "Remettre les étapes de réalisation de la duxelle de champignons dans le bon ordre :" and self.control_group_rank == 2:
            return self.text == "Suer sans coloration les échalotes"
        if self.question.text == "Remettre les étapes de réalisation de la duxelle de champignons dans le bon ordre :" and self.control_group_rank == 3:
            return self.text == "Ajouter les champignons"
        if self.question.text == "Remettre les étapes de réalisation de la duxelle de champignons dans le bon ordre :" and self.control_group_rank == 4:
            return self.text == "Réaliser une cheminée papier pour la cuisson"
        if self.question.text == "Remettre les étapes de réalisation de la duxelle de champignons dans le bon ordre :" and self.control_group_rank == 5:
            return self.text == "Surveiller l’évaporation de l’eau de végétation"
        if self.question.text == "L'ail se conserve mieux entier.":
            return re.search("(.*)(Vrai)(.*)", self.text)

        if self.question.text == "Classifiez ces poissons : Saint Pierre":
            return self.text == "Poisson plat à deux filets"
        if self.question.text == "Classifiez ces poissons : Maquereau":
            return self.text == "Poisson rond à deux filets"
        if self.question.text == "Classifiez ces poissons : Sole":
            return self.text == "Poisson plat à quatre filets"
        if self.question.text == "Classifiez ces poissons : Daurade":
            return self.text == "Poisson plat à deux filets"

        if self.question.text == "Je plaque du poisson : Pour optimiser la place dans les fours":
            return True
        if self.question.text == "Je plaque du poisson : Pour faire plaisir à mon chef":
            return False
        if self.question.text == "Je plaque du poisson : Pour faire beau":
            return False
        if self.question.text == "Je plaque du poisson : Pour limiter les manipulations":
            return True
        if self.question.text == "Je plaque du poisson : Par habitude":
            return False

        if self.question.text == "La cuisson braiser se fait au four":
            return True

        if self.question.text == "Combien de filets comptent les poissons suivants ? Saint Pierre":
            return self.text == "2 filets"
        if self.question.text == "Combien de filets comptent les poissons suivants ? Carrelet":
            return self.text == "4 filets"
        if self.question.text == "Combien de filets comptent les poissons suivants ? Sole":
            return self.text == "4 filets"
        if self.question.text == "Combien de filets comptent les poissons suivants ? Daurade":
            return self.text == "2 filets"
        return False
