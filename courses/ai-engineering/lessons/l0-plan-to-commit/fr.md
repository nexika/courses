# Du plan au commit

## Ce que vous saurez faire

- Utiliser le mode plan pour que Claude explore le code et propose un plan avant de rien modifier.
- Donner à Claude une vérification qu'il peut lancer, puis approuver le plan et le laisser implémenter
  la modification.
- Relire le résultat et faire le *commit* d'une seule modification, avec un message qui dit ce qu'elle
  fait.

## L'idée

Dans les deux premières leçons, vous avez approuvé les actions une par une et lu le *diff* qu'elles
laissaient. Cette leçon met ces gestes dans l'ordre, pour une modification complète.

Laisser Claude se lancer directement dans le code peut produire du code qui résout le mauvais
problème[^wrong-problem]. Le guide d'Anthropic donne le remède : séparer la recherche et la
planification de l'implémentation[^separate]. Le déroulé qu'il recommande a quatre phases[^phases] :
**explorer**, **planifier**, **implémenter**, **faire le commit**.

**Le mode plan.** Le mode plan demande à Claude de chercher et de proposer des modifications sans les
faire. Claude lit les fichiers, lance des commandes shell pour explorer et écrit un plan, mais ne
modifie pas votre code source[^plan-mode]. On y entre en appuyant sur `Shift+Tab` (jusqu'à ce que la
barre d'état affiche `⏸ plan mode on`), en lançant la session avec `claude --permission-mode plan`[^start-plan],
ou en mettant `/plan` devant une seule demande[^enter-plan].

Quand le plan est prêt, Claude le présente et vous demande comment continuer. Deux réponses comptent
ici :

- **Yes, manually approve edits** : approuver le plan, et relire chaque modification une à
  une[^approve-manual].
- **No, keep planning** : rester en mode plan et dire à Claude quoi changer[^keep-planning].

Approuver un plan fait sortir du mode plan, et Claude commence à modifier[^approve-exits]. Vous pouvez
aussi appuyer sur `Ctrl+G` pour ouvrir le plan dans votre éditeur de texte et le modifier vous-même
avant que Claude continue[^ctrl-g].

**Une vérification que Claude peut lancer.** Avant que Claude implémente quoi que ce soit, donnez-lui
un moyen de savoir quand il a fini : par exemple des tests[^check]. L'exemple du guide le dit sans détour : écrire un test qui échoue et reproduit le
problème, puis corriger[^failing-test]. Un test qui échoue décrit ce que vous voulez, et échoue
aujourd'hui parce que le code ne le fait pas encore.

**Une modification, un commit.** Un *commit* enregistre le contenu actuel de l'index avec un message
qui décrit les changements[^git-commit]. Faites un *commit* par modification, avec un message qui dit
ce qui a changé et pourquoi. Si la modification suivante tourne mal, vous pourrez toujours revenir à
celle-ci.

Voici la boucle entière sur un exemple. Vous voulez que `tip` refuse un pourcentage négatif.

- **Explorer et planifier**, en mode plan : « lis tip.py et test_tip.py ; je veux que tip() refuse un
  pourcentage négatif. Fais un plan. »
- **Relire le plan.** Ne modifie-t-il que `tip.py` ? Dit-il quelle erreur il lève ? Sinon, répondez
  **No, keep planning** et dites quoi changer.
- **Implémenter** : approuvez avec **Yes, manually approve edits**, lisez chaque modification, et
  demandez à Claude de lancer les tests.
- **Relire** : lisez `git diff` et la sortie des tests, comme dans la leçon précédente.
- **Faire le commit** : demandez à Claude de faire le *commit* avec un message descriptif[^commit-step],
  lisez la commande `git commit` dans la demande de permission, puis approuvez-la.

**Quand ne pas planifier.** Le mode plan est utile, mais il a un coût[^overhead] : il demande du temps et de l'attention en plus. Si vous pouvez
décrire le *diff* en une phrase, sautez le plan[^one-sentence]. La modification ci-dessus est aussi
petite que cela : on la planifie ici pour s'exercer aux étapes. Planifier sert surtout quand vous
n'êtes pas sûr de l'approche, quand la modification touche plusieurs fichiers, ou quand vous
connaissez mal le code[^planning-useful].

## Essayez

Reprenez le projet `tip-calc` de la première leçon. Lancez d'abord `git status` : si `tip.py` a
encore des changements de la première leçon, faites-en le *commit*, ou jetez-les avec
`git restore tip.py`. Lancez ensuite Claude Code en mode Manual, comme avant.

### Écrire d'abord la vérification

Enregistrez ceci sous le nom `test_tip.py`, à côté de `tip.py` :

```python
import unittest

from tip import tip


class TipTest(unittest.TestCase):
    def test_tip(self):
        self.assertEqual(tip(50, 15), 7.5)

    def test_a_negative_percent_is_refused(self):
        with self.assertRaises(ValueError):
            tip(50, -5)


if __name__ == "__main__":
    unittest.main()
```

Lancez `python3 -m unittest` dans le dossier `tip-calc`. Le nouveau test échoue, car `tip` ne refuse
pas encore un pourcentage négatif :

```text
F.
======================================================================
FAIL: test_a_negative_percent_is_refused (test_tip.TipTest.test_a_negative_percent_is_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tip-calc/test_tip.py", line 11, in test_a_negative_percent_is_refused
    with self.assertRaises(ValueError):
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 2 tests in 0.000s

FAILED (failures=1)
```

Les lignes exactes peuvent varier un peu selon votre version de Python. Faites le *commit* du test,
pour que le *diff* ne montre ensuite que la modification de Claude :

```bash
git add test_tip.py
git commit -m "Test that tip refuses a negative percent"
```

### Planifier

Dans Claude Code, appuyez sur `Shift+Tab` jusqu'à ce que la barre d'état affiche `⏸ plan mode on`, puis
tapez :

```text
read tip.py and test_tip.py. test_a_negative_percent_is_refused fails. Plan the smallest change to tip.py that makes it pass. Do not change the tests.
```

C'est-à-dire : « lis tip.py et test_tip.py. test_a_negative_percent_is_refused échoue. Planifie la plus
petite modification de tip.py qui le fasse passer. Ne modifie pas les tests. » Lisez le plan. S'il
touche un autre fichier que `tip.py`, ou modifie un test, choisissez **No, keep planning** et
dites-le.

### Implémenter et vérifier

Choisissez **Yes, manually approve edits**. Lisez la modification dans sa demande de permission avant
de l'approuver. Puis tapez :

```text
run python3 -m unittest and show me the output
```

C'est-à-dire : « lance `python3 -m unittest` et montre-moi la sortie ». Approuvez la commande. Les deux
tests doivent passer. Lisez la sortie vous-même : c'est votre preuve.

### Relire et faire le commit

Lancez `git diff` dans un autre terminal, ou `/diff` dans Claude Code. Seul `tip.py` doit avoir changé,
et seulement pour refuser un pourcentage négatif. Puis tapez :

```text
commit this change with a descriptive message
```

C'est-à-dire : « fais le commit de cette modification avec un message descriptif ». La demande de
permission montre la commande `git commit` et son message. Approuvez-la si le message dit ce qui a
changé. Lancez ensuite `git log --oneline` : il affiche le *commit* le plus récent en premier, donc la
correction en haut et le test juste en dessous.

## Erreurs fréquentes

**« Le mode plan rend la modification sûre. »** Le mode plan empêche Claude de modifier votre code
source pendant qu'il planifie[^plan-mode]. Le plan lui-même peut être faux. Lisez-le, et corrigez
Claude dès que vous voyez qu'il s'écarte de la route[^course-correct].

**« Il faut toujours planifier d'abord. »** Planifier a un coût[^overhead]. Pour une modification qui
tient en une phrase, sautez cette étape[^one-sentence].

**« Approuver le plan, c'est approuver chaque modification. »** Pas avec
**Yes, manually approve edits** : vous relisez encore chaque modification[^approve-manual]. L'option d'approbation **Yes, and use auto mode** lance le mode auto ; quand ce mode n'est
pas disponible, elle s'appelle **Yes, auto-accept edits**[^approve-auto]. En mode auto, la plupart des modifications de fichiers dans le dossier de votre projet sont approuvées sans demande[^auto-edits]. Ne la
choisissez que si vous relirez le *diff* ensuite.

**« Claude a écrit des tests, donc la modification est testée. »** Des tests écrits après le code
peuvent tester ce que fait le code plutôt que ce que vous vouliez. Écrivez ou lisez la vérification
avant l'implémentation, et regardez les changements de tests dans le *diff*.

**« Un seul commit en fin de journée suffit. »** Un *commit* qui mélange plusieurs modifications est
difficile à relire et difficile à annuler. Faites un *commit* par modification, une fois ses tests
passés et son *diff* lu.

**« Claude a fait le commit, donc l'historique est bon. »** Lisez le message du *commit* dans la
demande de permission. Il doit dire ce qui a changé. Sinon, répondez **No**, et dites quel message il
faut.

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/bill.py`. Sa fonction `split_bill(total_cents, tip_percent, people)` partage
une addition, pourboire compris, entre plusieurs personnes, en centimes entiers. Travailler en
centimes (des entiers) évite les surprises d'arrondi des nombres décimaux : les parts doivent faire
exactement l'addition et son pourboire. La *docstring* donne les règles : le pourboire est arrondi au
centime le plus proche (un demi-centime vers le haut), les centimes qui ne se partagent pas également
vont un par un aux premières personnes, et les entrées invalides lèvent `ValueError`. Les tests de
`exercise/tests/` sont la vérification.

Menez cette modification du plan au *commit* avec Claude Code :

- Copiez `exercise/starter/bill.py` et `exercise/tests/test_bill.py` dans un nouveau dossier, lancez-y
  `git init`, et faites le *commit* des deux fichiers.
- Lancez `python3 -m unittest` et voyez les tests échouer.
- Lancez Claude Code dans ce dossier en mode plan (`claude --permission-mode plan`), et demandez à
  Claude de lire les deux fichiers et de planifier une implémentation de
  `split_bill` qui fasse passer les tests sans les modifier. Relisez le plan. Demandez-lui de
  continuer à planifier si quelque chose n'est pas clair.
- Approuvez avec **Yes, manually approve edits**. Relisez chaque modification.
- Faites lancer les tests par Claude, avec leur sortie. Lisez `git diff` : seul `bill.py` doit
  changer.
- Demandez à Claude de faire le *commit* avec un message descriptif, et vérifiez ce message avant
  d'approuver.

### Lancer les tests

Votre dossier contient `test_bill.py` : lancez-y les tests, après chaque étape :

```bash
python3 -m unittest
```

Quand ils passent, vérifiez aussi votre `bill.py` avec la copie des tests du cours : copiez-le dans
`exercise/starter/`, à la place de l'ébauche, et lancez :

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Dans les deux cas, ils échouent tant que `split_bill` n'est pas juste. Une solution se trouve dans `exercise/solution/` ;
ne la regardez qu'après votre propre *commit*. Les tests vérifient le code, pas le chemin suivi : le
plan, la relecture et le *commit*, c'est à vous de les pratiquer. Le *commit* le plus récent, en haut de `git log`, ne doit modifier que `bill.py` (`git show --stat`
liste les fichiers qu'il a modifiés).

## Vérifiez vos acquis

Répondez aux questions de `quiz.json`. Si elles vous semblent difficiles, relisez les cinq étapes de l'exemple dans « L'idée ».

[^wrong-problem]: Documentation de Claude Code, Best practices for Claude Code.
[^separate]: Documentation de Claude Code, Best practices for Claude Code.
[^phases]: Documentation de Claude Code, Best practices for Claude Code.
[^plan-mode]: Documentation de Claude Code, Choose a permission mode.
[^start-plan]: Documentation de Claude Code, Best practices for Claude Code.
[^enter-plan]: Documentation de Claude Code, Choose a permission mode.
[^approve-manual]: Documentation de Claude Code, Choose a permission mode.
[^keep-planning]: Documentation de Claude Code, Choose a permission mode.
[^approve-exits]: Documentation de Claude Code, Choose a permission mode.
[^ctrl-g]: Documentation de Claude Code, Choose a permission mode.
[^check]: Documentation de Claude Code, Best practices for Claude Code.
[^failing-test]: Documentation de Claude Code, Best practices for Claude Code.
[^git-commit]: Documentation de Git, git-commit.
[^commit-step]: Documentation de Claude Code, Best practices for Claude Code.
[^overhead]: Documentation de Claude Code, Best practices for Claude Code.
[^one-sentence]: Documentation de Claude Code, Best practices for Claude Code.
[^planning-useful]: Documentation de Claude Code, Best practices for Claude Code.
[^course-correct]: Documentation de Claude Code, Best practices for Claude Code.
[^approve-auto]: Documentation de Claude Code, Choose a permission mode.
[^auto-edits]: Documentation de Claude Code, Choose a permission mode.
