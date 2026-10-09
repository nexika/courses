# Images et PDF

## Ce que vous saurez faire

- Envoyer une image ou un PDF à Claude dans une requête, sous forme de bloc de contenu, en connaissant les
  formats et les limites.
- Estimer le coût d'une image en tokens avant de l'envoyer.
- Vérifier ce que Claude extrait d'une image ou d'un PDF avant de l'utiliser, et savoir quand une personne
  doit regarder.

## L'idée

Jusqu'ici, vous avez envoyé du texte à Claude. Claude sait aussi comprendre et analyser des
images[^v-what]. Et vous pouvez l'interroger sur le texte, les images, les graphiques et les tableaux d'un
PDF[^p-what]. Un usage possible consiste à transformer un document en données structurées, comme les champs
d'une facture[^p-what].

**Une image est un bloc de contenu**

Dans la leçon « Votre premier appel à l'API », le `content` d'un tour utilisateur était une chaîne, et le
`content` d'une réponse une liste de blocs. Le `content` d'un tour utilisateur peut aussi être une liste de
blocs de contenu, et une image en est un[^v-sources]. L'API accepte une image de trois façons : les octets de l'image dans la
requête, encodés en `base64` ; une URL où l'image est en ligne ; ou un `file_id` de la Files API, où vous
envoyez un fichier une fois pour y faire référence ensuite autant de fois que vous voulez[^v-sources].
Voici la première façon :

```json
{"role": "user", "content": [
  {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
  {"type": "text", "text": "What does this receipt say?"}
]}
```

`base64` transforme n'importe quels octets en lettres, chiffres et quelques signes, pour qu'un fichier puisse
voyager dans du JSON. En Python, le contenu brut d'un fichier est une valeur `bytes`, écrite comme
`b"GIF89a"` ; dedans, `\x89` est un octet, écrit en hexadécimal (voir plus bas). `.decode("ascii")`
transforme les octets `base64` en chaîne ordinaire, ce qu'exige JSON ; ASCII est le jeu de base des
lettres anglaises, des chiffres et des signes. Le *type de média* (*media type*) est une étiquette qui dit quel genre de fichier
c'est, par exemple `image/png`. Claude accepte les images JPEG, PNG, GIF et WebP ; pour une image animée,
il n'utilise que la première trame[^v-formats]. Placez l'image avant votre question : Claude fonctionne
mieux ainsi, même si l'autre ordre marche aussi[^v-order].

Ne vous fiez pas au nom d'un fichier pour connaître son type. Regardez ses premiers octets : tout fichier
PNG commence par les huit mêmes octets, `89 50 4E 47 0D 0A 1A 0A` en hexadécimal[^png-sig], et les autres
formats ont leurs propres signatures, listées dans l'exercice. (On écrit d'habitude les octets en
hexadécimal, une façon d'écrire les nombres qui utilise aussi les lettres de A à F.)

**Un PDF est un bloc de document**

Un PDF va dans un bloc de type `document`, avec le type de média `application/pdf`[^p-type]. Comme une image, il peut
être envoyé par URL, en `base64` ou par `file_id`[^p-ways]. L'API transforme chaque page en image et
extrait aussi le texte de chaque page, et Claude lit les deux. C'est ainsi qu'il peut répondre à des
questions sur des graphiques et des schémas, pas seulement sur le texte[^p-how].

**Le coût et les limites**

Claude voit une image comme des carrés de 28 × 28 pixels ; chaque carré est un *token visuel* (*visual
token*)[^v-cost]. Une image coûte ⌈width / 28⌉ × ⌈height / 28⌉ tokens visuels, où ⌈ ⌉ veut dire
« arrondi au-dessus »[^v-cost]. Une image de 1000 × 1000 coûte 36 × 36 = 1296 tokens visuels[^v-table].
Les images qui dépassent les limites d'un modèle sont réduites avant que Claude les voie[^v-downscale].
Sur Claude 4.7 et les modèles suivants, la limite est de 2576 pixels sur le grand côté et de 4784 tokens
visuels[^v-tiers]. Claude Opus 5.5, le modèle de ce cours, est l'un de ces modèles suivants : ces limites
s'appliquent donc à lui[^v-tiers].
Sur ce modèle, une image de 1920 × 1080 coûte 2691 tokens visuels, sans être réduite[^v-table-hd]. N'envoyez pas une image plus grande que ce que la tâche demande.

Une page de PDF coûte des tokens deux fois. Le texte de chaque page utilise en général de 1 500 à 3 000
tokens, et l'image de chaque page est comptée comme n'importe quelle image[^p-cost]. Les PDF denses, avec
de petites polices, des tableaux complexes ou beaucoup de graphismes, peuvent remplir la fenêtre de
contexte avant la limite de pages[^p-dense].

Les principales limites sur l'API Claude. Claude est aussi proposé par d'autres services cloud, comme
Amazon Bedrock et Google Cloud, et certaines limites y sont plus basses[^v-size] :

- Une image fait au plus 8000 × 8000 pixels[^v-dims] (ou, par prudence sur tous les services,
  2000 × 2000 quand une requête contient plus de 20 images[^v-many]), et au plus 10 Mo une fois encodée en
  `base64`[^v-size].
- Une requête contient jusqu'à 600 images, ou 100 sur les modèles dont la fenêtre de contexte est de 200k
  tokens[^v-count].
- Une requête avec PDF contient jusqu'à 600 pages, ou 100 quand la fenêtre de contexte fait moins de 1M
  tokens ; la requête entière fait au plus 32 Mo sur l'API Claude (les autres services diffèrent), et le PDF ne doit avoir ni mot de passe ni
  chiffrement[^p-limits].

**Vérifier ce que Claude extrait**

Claude peut se tromper sur ce qu'il voit. Il peut faire des erreurs sur des images de mauvaise qualité,
tournées ou très petites (moins de 200 pixels), ses comptages de nombreux petits objets sont
approximatifs, et il ne sait pas dire si une image a été créée par une IA[^v-limits]. Il ne voit pas les
métadonnées d'une image, comme la date enregistrée dans une photo[^v-meta]. Les PDF ont les mêmes limites,
puisque Claude lit leurs pages comme des images[^p-vision]. Le guide d'Anthropic demande de relire et de
vérifier ce que Claude dit des images, et de ne pas l'utiliser pour des tâches qui exigent une précision
parfaite sans qu'une personne contrôle[^v-verify].

Traitez donc une extraction comme toute autre sortie du modèle, comme dans la leçon sur les sorties JSON :
vérifiez-la avant de l'utiliser. Trois contrôles aident :

1) **La forme :** le JSON contient les champs dont vous avez besoin, avec les bons types (votre `validate`
   de cette leçon).
2) **Les sommes :** les nombres concordent entre eux. Sur une facture, les lignes font le total.
3) **La source :** les valeurs figurent dans quelque chose que vous avez obtenu autrement, comme
   l'enregistrement du système qui a émis la facture.

Quand un contrôle échoue, ne devinez pas : envoyez le document à une personne.

## Essayez

### Sans clé : construire une requête et vérifier une extraction

Ce script lit un tout petit PNG, l'image d'exemple du guide d'Anthropic sur la vision[^v-example], écrite en texte
`base64`. Il vérifie les premiers octets du fichier, lit sa taille, compte les tokens visuels et
construit la requête. Puis il vérifie deux extractions d'exemple d'une facture : l'une correcte, l'autre
où un montant a été mal lu. Enregistrez-le sous `look_and_check.py` dans le dossier de la leçon et lancez
`python3 look_and_check.py` depuis ce dossier :

```python
"""Build an image request and check an extraction, offline. No network, no key."""
import base64
import json
import math
import struct
from pathlib import Path

# 1. A tiny PNG (one pixel), written as base64 text. Real code reads a file: Path("photo.png").read_bytes()
data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")
print("starts like a PNG:", data.startswith(b"\x89PNG\r\n\x1a\n"))
width, height = struct.unpack(">II", data[16:24])
print("size:", width, "x", height)

# 2. What it costs: one visual token per 28 x 28 patch.
for w, h in ((width, height), (1000, 1000), (1920, 1080)):
    print(f"{w} x {h}:", math.ceil(w / 28) * math.ceil(h / 28), "visual tokens")

# 3. The request: the image first, then the question.
request = {"model": "claude-opus-5-5", "max_tokens": 1024, "messages": [{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                 "data": base64.standard_b64encode(data).decode("ascii")}},
    {"type": "text", "text": "What colour is this pixel?"}]}]}
print(json.dumps(request)[:160], "...")

# 4. Check an extraction: do the line amounts add up to the total?
folder = Path("exercise/tests")
for name in ("sample_extracted_ok.json", "sample_extracted_misread.json"):
    invoice = json.loads((folder / name).read_text(encoding="utf-8"))
    lines = sum(line["amount"] for line in invoice["lines"])
    print(name, "lines add up to", lines, "total says", invoice["total"],
          "OK" if abs(lines - invoice["total"]) < 0.005 else "CHECK BY HAND")
```

`math.ceil` arrondit au-dessus, comme ⌈ ⌉ plus haut. `struct.unpack(">II", ...)` lit deux nombres entiers
de quatre octets chacun, la largeur et la hauteur ; `>` veut dire gros-boutiste (*big-endian*) : le
premier octet compte le plus, comme le premier chiffre d'un nombre écrit.
Un PNG est fait de *chunks*, des morceaux de données étiquetés, et les données du premier chunk commencent
par la largeur et la hauteur[^png-ihdr] ; dans le fichier, elles viennent juste après les seize premiers octets.

Dans l'extraction mal lue, les lignes totalisent 1404,5, moins que le total : un montant est faux, et le
contrôle de somme l'a vu sans savoir lequel. Le script accepte un écart minuscule, car les nombres à
virgule ne sont pas exacts en Python : `0.1 + 0.2` donne `0.30000000000000004`.

Les extractions d'exemple ont la forme de vraies extractions mais ont été écrites à la main ; la facture
est inventée.

### Avec votre propre clé (facultatif)

Ceci envoie une vraie image : il faut une clé, et ses tokens sont facturés. Préparez la clé et le SDK comme
dans la leçon « Votre premier appel à l'API ». Utilisez une photo ou un scan d'un de vos tickets de caisse,
enregistré sous `receipt.jpg` :

```python
import base64
from pathlib import Path

import anthropic

data = Path("receipt.jpg").read_bytes()
client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                     "data": base64.standard_b64encode(data).decode("ascii")}},
        {"type": "text", "text": "List each item and its price as JSON, then the total."},
    ]}],
)
print("".join(block.text for block in message.content if block.type == "text"))
print("input tokens:", message.usage.input_tokens)
```

Pour un PDF, utilisez `"type": "document"` et `"media_type": "application/pdf"`. Comparez ce qui revient
avec le ticket lui-même, ligne par ligne.

## Erreurs fréquentes

- **Faire confiance à l'extraction parce qu'elle a l'air propre.** Un JSON net peut contenir un nombre mal
  lu. Vérifiez la forme, les sommes et la source[^v-verify].
- **Deviner le type d'après le nom du fichier.** Un fichier appelé `scan.png` peut être un JPEG, et le type
  de média envoyé doit correspondre aux octets. Lisez les premiers octets[^png-sig].
- **Envoyer des images énormes.** Elles coûtent plus de tokens et sont réduites de toute façon[^v-downscale].
  Réduisez-les vous-même à ce que la tâche demande.
- **Placer la question avant l'image.** Cela marche, mais Claude fonctionne mieux avec l'image
  d'abord[^v-order].
- **Demander à Claude de compter beaucoup de petites choses ou de nommer une personne.** Les comptages sont
  approximatifs, et Claude n'identifie pas les personnes sur les images[^v-limits].
- **Envoyer un fichier Word ou Excel comme document.** Les formats comme `.docx` et `.xlsx` ne sont pas
  acceptés dans les blocs de document ; convertissez-les d'abord en texte ou en PDF[^p-binary].

## Votre exercice

### Ce qu'il faut construire

Ouvrez `exercise/starter/media.py`. Il vous donne les signatures de fichiers et les limites sous forme de
constantes. Écrivez cinq fonctions ; elles tournent hors ligne, et les tests fabriquent leurs propres
petits fichiers PNG.

- `media_type(data)` renvoie le type de média d'après les premiers octets du fichier, ou lève
  `ValueError`.
- `content_block(data)` renvoie le bloc d'image ou de document, avec les octets en `base64`. Elle refuse
  une image dont le texte en `base64` dépasse la limite de 10 Mo[^v-size].
- `png_size(data)` renvoie la largeur et la hauteur d'un PNG, lues dans son premier chunk (le fichier de
  départ explique où elles se trouvent).
- `visual_tokens(width, height)` renvoie le coût en tokens visuels, et lève `ValueError` pour une image
  que l'API réduirait, pour que vous la redimensionniez d'abord vous-même.
- `check_invoice(extracted, source_text)` renvoie les problèmes d'une facture extraite par Claude : champs
  manquants, lignes qui ne font pas le total, et valeurs absentes du texte source.

### Lancez les tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Les tests échouent tant que vos fonctions ne marchent pas. Une solution se trouve dans
`exercise/solution/` : essayez d'abord, puis comparez.

## Vérifiez vos acquis

Faites le quiz de cette leçon. Si une question vous pose problème, relisez « Le coût et les limites » et
« Vérifier ce que Claude extrait ».

[^v-what]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-what]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-sources]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-formats]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-order]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^png-sig]: Portable Network Graphics (PNG) Specification (Third Edition), <https://www.w3.org/TR/png-3/>
[^p-ways]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-how]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-cost]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-tiers]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-cost]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-dense]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-dims]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-size]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-count]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-limits]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-limits]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-meta]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-vision]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-verify]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-table]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^png-ihdr]: Portable Network Graphics (PNG) Specification (Third Edition), <https://www.w3.org/TR/png-3/>
[^v-downscale]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-table-hd]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-many]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-example]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-type]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-binary]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
