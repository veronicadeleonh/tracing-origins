"""object_types.py — capa de clasificación "tipo de pieza" (18/09).

No es layer 1/2/3 en el sentido estricto del modelo de datos del proyecto
(ver CLAUDE.md) — es una inferencia nuestra derivada del campo `objectName`
de layer 1, en el mismo espíritu que la geocodificación de layer 2
(`geocode.py`): no viene tal cual del museo, la calculamos nosotros a partir
de un campo crudo.

Vocabulario cerrado de 14 categorías (ES/EN), diseñado y aprobado por la
usuaria el 18/09 — multi-etiqueta (1-3 tags por pieza, mismo mecanismo que
`context_flags` en `data/enrichment/context.csv`: semicolon-separated,
closed vocabulary). `kudurru` se pliega dentro de `stela_inscription` a
propósito (resolución por defecto acordada con la usuaria); `sculpture` y
`stela_inscription` quedan como categorías separadas, también a pedido
explícito.

`objectName` es texto crudo, específico por museo (inglés para Met/BM,
francés para Louvre/Quai Branly) y muy granular (~360 valores distintos en
total entre los 4 museos) — no hay traducción/normalización posible sin una
tabla de mapeo exacta por museo, así que este módulo expone 4 diccionarios
de mapeo EXACTO (no keyword/substring, a diferencia de `geocode.py` — el
campo `objectName` es mucho más corto y specific que el texto libre de
`placeOfDiscovery`, así que no hace falta ese mecanismo acá) más una función
`classify_object_type(source_museum, object_name)` que hace el lookup y cae
a `["unclassified"]` si el valor no está en la tabla (valor vacío, o un
`objectName` nuevo que todavía no se revisó a mano).

Igual que las listas de keywords de `geocode.py`, estas tablas son un
mecanismo incremental: cubren los ~360 valores existentes al 18/09, pero un
`fetch_*.py` futuro puede traer `objectName` nuevos sin match — quedan como
`unclassified` hasta que se revisen y se agreguen a mano, no es un bug.

Criterio general seguido para casos ambiguos (mismo espíritu de "no inventar
precisión que no tenemos" que ya rige el resto del pipeline): herramientas o
partes de fabricación sin forma reconocible por sí mismas (heddle pulley,
spindle whorl, moldes, tapones de cerradura, instrumentos científicos) se
dejan en `unclassified` en vez de forzarlas dentro de una categoría que no
las describe bien.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Vocabulario cerrado — 14 categorías, (label_es, label_en)
# ---------------------------------------------------------------------------

OBJECT_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "sculpture": ("Escultura", "Sculpture"),
    "stela_inscription": ("Estela e inscripción", "Stela and inscription"),
    "vessel_ceramic": ("Vasija y cerámica", "Vessel and ceramics"),
    "jewelry": ("Joyería y ornamento", "Jewelry and ornament"),
    "textile": ("Textil y vestimenta", "Textile and clothing"),
    "weapon": ("Arma", "Weapon"),
    "amulet_ritual": ("Objeto ritual y religioso", "Ritual and religious object"),
    "architectural_element": ("Elemento arquitectónico", "Architectural element"),
    "manuscript_document": (
        "Manuscrito, sello y documento",
        "Manuscript, seal and document",
    ),
    "coin": ("Moneda", "Coin"),
    "musical_instrument": ("Instrumento musical", "Musical instrument"),
    "furniture": ("Mobiliario", "Furniture"),
    "painting_drawing": ("Pintura y dibujo", "Painting and drawing"),
    "unclassified": ("Sin clasificar", "Unclassified"),
}

# Orden "lógico" sugerido para la UI (figurativo -> texto -> sin clasificar),
# no alfabético — mismo criterio que ya usa `contextFlagLabels` en el
# frontend (ordenado por frecuencia ahí, acá por afinidad temática).
OBJECT_TYPE_ORDER: list[str] = [
    "sculpture",
    "stela_inscription",
    "vessel_ceramic",
    "jewelry",
    "textile",
    "weapon",
    "amulet_ritual",
    "architectural_element",
    "manuscript_document",
    "coin",
    "musical_instrument",
    "furniture",
    "painting_drawing",
    "unclassified",
]

_UNCLASSIFIED = ["unclassified"]

# ---------------------------------------------------------------------------
# Met — objectName crudo (inglés) -> tags. 116 valores distintos al 18/09.
# ---------------------------------------------------------------------------

MET_OBJECT_TYPE_MAP: dict[str, list[str]] = {
    "Figure": ["sculpture"],
    "Fragment": ["unclassified"],
    "Lamp": ["vessel_ceramic"],
    "Bowl": ["vessel_ceramic"],
    "Relief": ["sculpture"],
    "Hanging scroll": ["painting_drawing"],
    "Ink tablet": ["manuscript_document"],
    "Coat": ["textile"],
    "Jug": ["vessel_ceramic"],
    "Crown": ["jewelry"],
    "Spear": ["weapon"],
    "Heddle pulley": ["unclassified"],
    "Folding fan mounted as an album leaf": ["painting_drawing"],
    "Tile": ["architectural_element"],
    "Vase with cover": ["vessel_ceramic"],
    "Bracelet": ["jewelry"],
    "Head of Medusa": ["sculpture"],
    "Aryballos": ["vessel_ceramic"],
    "Sculpture": ["sculpture"],
    "Jar": ["vessel_ceramic"],
    "Cylinder seal": ["manuscript_document"],
    "": ["unclassified"],
    "Vase, monkey, baby": ["vessel_ceramic"],
    "Basin": ["vessel_ceramic"],
    "Jar, wine or beer": ["vessel_ceramic"],
    "Figurine": ["sculpture"],
    "Ink stick": ["manuscript_document"],
    "Spearhead": ["weapon"],
    "Sticks": ["unclassified"],
    "Plugs": ["jewelry"],
    "Illustrated single work": ["painting_drawing"],
    "Cape": ["textile"],
    "Kaftan": ["textile"],
    "Robe": ["textile"],
    "Dress": ["textile"],
    "Headscarf": ["textile"],
    "Brooch": ["jewelry"],
    "Skirt": ["textile"],
    "Shoes": ["textile"],
    "Shirt(?)": ["textile"],
    "Amphora": ["vessel_ceramic"],
    "Juglet": ["vessel_ceramic"],
    "Strigil blade": ["unclassified"],
    "Strigil": ["unclassified"],
    "Ring": ["jewelry"],
    "Portrait bust of a woman": ["sculpture"],
    "Head of a woman": ["sculpture"],
    "Skyphos, glaux": ["vessel_ceramic"],
    "Olpe": ["vessel_ceramic"],
    "Lekythos": ["vessel_ceramic"],
    "Nose ornament": ["jewelry"],
    "Spindle whorl": ["unclassified"],
    "Necklace": ["jewelry"],
    "Disk": ["unclassified"],
    "Mold": ["unclassified"],
    "Dome": ["architectural_element"],
    "Canoe prow": ["sculpture"],
    "Twin figure": ["sculpture"],
    "Whistle": ["musical_instrument"],
    "Bottle": ["vessel_ceramic"],
    "Pendant": ["jewelry"],
    "Stamp seal": ["manuscript_document"],
    "Cuneiform tablet": ["manuscript_document"],
    "Beads": ["jewelry"],
    "Ornament": ["jewelry"],
    "Cuneiform tablet case": ["manuscript_document"],
    "Bead": ["jewelry"],
    "Harness or bridle fitting (?)": ["unclassified"],
    "Earring": ["jewelry"],
    "Foundation figure": ["sculpture"],
    "Scarf": ["textile"],
    "Hanging": ["textile"],
    "Textile fragment": ["textile"],
    "Dish": ["vessel_ceramic"],
    "Fragment of a cup": ["vessel_ceramic"],
    "Handle": ["unclassified"],
    "False door, Neferiu, Wedjebet": ["stela_inscription", "architectural_element"],
    "Dish, libation": ["vessel_ceramic"],
    "Statuette, male beer-maker": ["sculpture"],
    "Statue, Merti's wife, standing, Mitry": ["sculpture"],
    "Weight, 5 deben": ["unclassified"],
    "Relief, king Khufu's cattle": ["sculpture"],
    "Relief, ship under sail": ["sculpture"],
    "Relief, archers": ["sculpture"],
    "Head fragment, King Khafre": ["sculpture"],
    "Music, sistrum, Teti, papyrus, falcon": ["musical_instrument"],
    "Statue, standing pair, Memi, Sabu": ["sculpture"],
    "Statue, Nikare, scribe": ["sculpture"],
    "Statue group, Nikare, wife, daughter": ["sculpture"],
    "Statue, seated pair, Demedji, Hennutsen": ["sculpture"],
    "Statue, striding man": ["sculpture"],
    "Tile, apartments of King Djoser": ["architectural_element"],
    "Statuette, woman and child": ["sculpture"],
    "Statue, kneeling captive": ["sculpture"],
    "False door, tomb of Metjetji": ["stela_inscription", "architectural_element"],
    "Head, reserve": ["sculpture"],
    "Offering stand, king Khafre": ["furniture"],
    "Offering table": ["furniture"],
    "False Door Niche block, Akhtihotep, corner": [
        "stela_inscription",
        "architectural_element",
    ],
    "Relief, tomb of Akhtihotep": ["sculpture"],
    "Relief, Chapel of Nikauhor and Sekhemhathor": ["sculpture"],
    "Statue, Tjeteti, young man": ["sculpture"],
    "Statue, Tjeteti, middle age": ["sculpture"],
    "Mummified leg of beef case": ["unclassified"],
    "Mummified goose case": ["unclassified"],
    "Mummified duck case": ["unclassified"],
    'Model, "Opening of the Mouth" ritual equipment': ["amulet_ritual"],
    "Ewer": ["vessel_ceramic"],
    "Vessel, Ewer": ["vessel_ceramic"],
    'Pot, "nw" pot, miniature': ["vessel_ceramic"],
    "Persian Travelogue": ["manuscript_document"],
    "Urn": ["vessel_ceramic"],
    "Winged bull": ["sculpture"],
    'Drawing, "Drone Hits Great Ziggurat of Ur"': ["painting_drawing"],
    'Time-Based Media; Video; Animation; Drawings; "Drone Hits Great Ziggurat of Ur"': [
        "painting_drawing"
    ],
    "Pendant mask": ["jewelry", "sculpture"],
}

# ---------------------------------------------------------------------------
# Louvre — objectName crudo (francés) -> tags. 117 valores distintos al 18/09.
# ---------------------------------------------------------------------------

LOUVRE_OBJECT_TYPE_MAP: dict[str, list[str]] = {
    "statue": ["sculpture"],
    "Coupe (Vase, récipient)": ["vessel_ceramic"],
    "figurine": ["sculpture"],
    "stèle": ["stela_inscription"],
    "hache": ["weapon"],
    "kudurru": ["stela_inscription"],
    "statue (fragment, tête)": ["sculpture"],
    "Plat (Vase, récipient)": ["vessel_ceramic"],
    "Aiguière / Aquamanile (Vase, récipient->Verseuse)": ["vessel_ceramic"],
    "statue (fragment)": ["sculpture"],
    "cratère": ["vessel_ceramic"],
    "amphore": ["vessel_ceramic"],
    "stèle cintrée": ["stela_inscription"],
    "statuette": ["sculpture"],
    "stèle (fragment)": ["stela_inscription"],
    "relief": ["sculpture"],
    "vase": ["vessel_ceramic"],
    "tablette": ["manuscript_document"],
    "relief architectural ; bloc de parement": ["architectural_element", "sculpture"],
    "métope (fragment)": ["sculpture", "architectural_element"],
    "Carreau de revêtement (Élément d'architecture, décor intérieur et extérieur, huisserie->Décor architectural)": [
        "architectural_element"
    ],
    "modèle": ["unclassified"],
    "statue de couple": ["sculpture"],
    "stèle cintrée ; stèle à un registre": ["stela_inscription"],
    "sarcophage": ["sculpture"],
    "élément architectural": ["architectural_element"],
    "mors": ["unclassified"],
    "inscription": ["stela_inscription"],
    "groupe statuaire": ["sculpture"],
    "Vantail (Élément d'architecture, décor intérieur et extérieur, huisserie->Élément d'architecture->Porte)": [
        "architectural_element"
    ],
    "Sculpture ; Statue, statuette, figurine": ["sculpture"],
    "Tapis": ["textile"],
    "statue de couple (fragment)": ["sculpture"],
    "papyrus funéraire": ["manuscript_document"],
    "statue ; pilier osiriaque (fragment)": ["sculpture"],
    "figurine ; enseigne divine": ["sculpture"],
    "relief mural (fragment)": ["sculpture", "architectural_element"],
    "cuiller à fard à la nageuse": ["unclassified"],
    "pendentif": ["jewelry"],
    "statue de scribe assis en tailleur": ["sculpture"],
    "palette à fard (fragment)": ["unclassified"],
    "couteau": ["weapon"],
    "ostracon figuré": ["manuscript_document"],
    "pyramidion": ["architectural_element"],
    "figurine d'Osiris": ["sculpture"],
    "figurine ; élément de meuble (?) ; serrure (?)": ["sculpture", "furniture"],
    "statue cube": ["sculpture"],
    "statue colossale": ["sculpture"],
    "naos (fragment)": ["architectural_element"],
    "chevalière à chaton renflé": ["jewelry"],
    "stèle cintrée ; stèle biface": ["stela_inscription"],
    "stèle cintrée (fragmentaire) ; stèle à deux registres": ["stela_inscription"],
    "plafond ; relief mural": ["architectural_element"],
    "stèle frontière ; stèle cintrée (fragments)": ["stela_inscription"],
    "figurine ; statuette": ["sculpture"],
    "statue guérisseuse ; statue stéléphore": ["sculpture"],
    "amulette": ["amulet_ritual"],
    "parchemin": ["manuscript_document"],
    "icône": ["painting_drawing"],
    "chapelle de mastaba": ["architectural_element"],
    "Aiguière en cristal de roche du trésor de Saint-Denis": ["vessel_ceramic"],
    "statue ; vase": ["sculpture", "vessel_ceramic"],
    "vase (objet votif)": ["vessel_ceramic"],
    "statue (tête)": ["sculpture"],
    "stèle (fragment : 7)": ["stela_inscription"],
    "pendeloque": ["jewelry"],
    "placage de meuble": ["furniture"],
    "placage de meuble (fragment) ; lame": ["furniture"],
    "autel ; figurine": ["architectural_element", "sculpture"],
    "peinture murale": ["painting_drawing"],
    "tablette (fragment)": ["manuscript_document"],
    "lance": ["weapon"],
    "poignard ; fourreau": ["weapon"],
    "autel (fragment)": ["architectural_element"],
    "panneau de briques": ["architectural_element"],
    "élément de mobilier": ["furniture"],
    "stamnos": ["vessel_ceramic"],
    "statue ; base de statue": ["sculpture"],
    "casque": ["weapon"],
    "statuette ; ex-voto": ["sculpture"],
    "arula": ["architectural_element"],
    "dinos ; support de dinos": ["vessel_ceramic"],
    "coupe": ["vessel_ceramic"],
    "lécythe": ["vessel_ceramic"],
    "mosaïque": ["architectural_element"],
    "métope": ["sculpture", "architectural_element"],
    "couvercle de sarcophage (?) ; couvercle d'urne (?)": [
        "sculpture",
        "vessel_ceramic",
    ],
    "relief architectural": ["architectural_element", "sculpture"],
    "Poids de tapis (Objet divers)": ["textile"],
    "Bassin (Vase, récipient)": ["vessel_ceramic"],
    "Coffre (Mobilier) ; Coffret (Accessoire personnel, boîte, étui)": ["furniture"],
    "Moule et élément pour estamper (Équipement pour l'artisanat et l'industrie)": [
        "unclassified"
    ],
    "Cadenas (Serrurerie, ferronnerie)": ["unclassified"],
    "Robinet (Objet divers)": ["unclassified"],
    "Edicule (Objet divers)": ["architectural_element"],
    "Nécessaire d'orfèvre (Équipement pour l'artisanat et l'industrie) ; Coffret (Accessoire personnel, boîte, étui)": [
        "furniture"
    ],
    "Globe céleste (Instrument scientifique)": ["unclassified"],
    "Plateau (Vase, récipient)": ["vessel_ceramic"],
    "Coupe (Vase, récipient) ; Gemme (Gemme et pierre dure)": [
        "vessel_ceramic",
        "jewelry",
    ],
    "Album (= Muraqqa) (Art du livre)": ["manuscript_document"],
    "Pyxide (Accessoire personnel, boîte, étui->Boîte) ; Tabletterie": [
        "vessel_ceramic"
    ],
    "Vase (Vase, récipient)": ["vessel_ceramic"],
    "Étoile (Élément d'architecture, décor intérieur et extérieur, huisserie->Décor architectural->Carreau de revêtement)": [
        "architectural_element"
    ],
    "Gobelet (Vase, récipient)": ["vessel_ceramic"],
    "Chandelier (Instrument d'éclairage)": ["furniture"],
    "Textile divers": ["textile"],
    "Vase (Vase, récipient) ; Statue, statuette, figurine": [
        "vessel_ceramic",
        "sculpture",
    ],
    "Sculpture": ["sculpture"],
    "Bouteille (Vase, récipient)": ["vessel_ceramic"],
    "Lampe (Instrument d'éclairage)": ["vessel_ceramic"],
    "Kanjar (Arme et équipement militaire->Poignard)": ["weapon"],
    "Bol (Vase, récipient)": ["vessel_ceramic"],
    "Coffret (Accessoire personnel, boîte, étui) ; Tabletterie": ["furniture"],
    "Élément d'architecture (Élément d'architecture, décor intérieur et extérieur, huisserie)": [
        "architectural_element"
    ],
    "Vantail (Élément d'architecture, décor intérieur et extérieur, huisserie->Élément d'architecture->Porte) ; Mobilier": [
        "architectural_element",
        "furniture",
    ],
}

# ---------------------------------------------------------------------------
# British Museum — objectName crudo (inglés) -> tags. 56 valores al 18/09.
# ---------------------------------------------------------------------------

BM_OBJECT_TYPE_MAP: dict[str, list[str]] = {
    "adze": ["weapon"],
    "figure": ["sculpture"],
    "plaque": ["sculpture"],
    "armlet": ["jewelry"],
    "animal remains": ["unclassified"],
    "bag": ["textile"],
    "bell": ["musical_instrument"],
    "block": ["architectural_element"],
    "axe": ["weapon"],
    "altar": ["architectural_element"],
    "robe": ["textile"],
    "coin": ["coin"],
    "necklace": ["jewelry"],
    "bead": ["jewelry"],
    "vessel": ["vessel_ceramic"],
    "bowl": ["vessel_ceramic"],
    "club": ["weapon"],
    "statue": ["sculpture"],
    "box": ["furniture"],
    "reliquary": ["amulet_ritual"],
    "signet-ring": ["jewelry"],
    "bottle (백자반구병\n白磁盤口甁)": ["vessel_ceramic"],
    "altar-piece": ["architectural_element"],
    "architecture": ["architectural_element"],
    "book": ["manuscript_document"],
    "gong-stand": ["musical_instrument"],
    "cap": ["textile"],
    "head-dress": ["textile"],
    "shield": ["weapon"],
    "processional cross": ["amulet_ritual"],
    "arrow": ["weapon"],
    "anklet": ["jewelry"],
    "bangle": ["jewelry"],
    "spear": ["weapon"],
    "beam (?)": ["architectural_element"],
    "model": ["unclassified"],
    "arm-dagger": ["weapon"],
    "bracelet": ["jewelry"],
    "baby-carrier": ["textile"],
    "shield (?)": ["weapon"],
    "vase": ["vessel_ceramic"],
    "water-bottle": ["vessel_ceramic"],
    "apron": ["textile"],
    "beaker": ["vessel_ceramic"],
    "adorno": ["jewelry"],
    "artefact": ["unclassified"],
    "cape": ["textile"],
    "mask": ["sculpture", "amulet_ritual"],
    "canoe": ["unclassified"],
    "alabastron": ["vessel_ceramic"],
    "obelisk": ["architectural_element"],
    "door-sill": ["architectural_element"],
    "cylinder": ["unclassified"],
    "jacket (sheepskin jacket (farwah/farweh))": ["textile"],
    "stela": ["stela_inscription"],
    "amphora": ["vessel_ceramic"],
}

# ---------------------------------------------------------------------------
# Quai Branly — objectName crudo (francés) -> tags. 67 valores al 18/09.
# ---------------------------------------------------------------------------

QUAIBRANLY_OBJECT_TYPE_MAP: dict[str, list[str]] = {
    "Peigne de protection contre les maladies": ["amulet_ritual"],
    "Amulette": ["amulet_ritual"],
    "Objet indéterminé": ["unclassified"],
    "Plat": ["vessel_ceramic"],
    "Amulette anthropomorphe": ["amulet_ritual"],
    "Marupaï": ["sculpture", "painting_drawing"],
    "Masque": ["sculpture", "amulet_ritual"],
    "Pot": ["vessel_ceramic"],
    "Massue": ["weapon"],
    "Éventail": ["textile"],
    "Jarre": ["vessel_ceramic"],
    "Broche": ["jewelry"],
    "Les Anglais chassés de l'ïle Saint Christophe, 1666": ["coin"],
    "La prise du fort de Tabago, 1677": ["coin"],
    "Collier": ["jewelry"],
    "Gargoulette": ["vessel_ceramic"],
    "Bracelets": ["jewelry"],
    "Fibules": ["jewelry"],
    "Bol à deux anses": ["vessel_ceramic"],
    "Amulette : anthropomorphe": ["amulet_ritual"],
    "Masque miniature de diable": ["sculpture", "amulet_ritual"],
    "Bouclier": ["weapon"],
    "Petit masque": ["sculpture", "amulet_ritual"],
    "Bâton cérémoniel": ["amulet_ritual"],
    "Pendentif": ["jewelry"],
    "Objet non identifié": ["unclassified"],
    "Pied de lit": ["furniture"],
    "Défense d'éléphant travaillée": ["sculpture"],
    "Les ambassadeurs du roi de Siam, 1686": ["coin"],
    "Brassard": ["jewelry"],
    "Charme de guerre": ["amulet_ritual"],
    "Chasse-mouches": ["amulet_ritual"],
    "Lance cérémonielle": ["weapon", "amulet_ritual"],
    "Lampe": ["vessel_ceramic"],
    "Vase à eau": ["vessel_ceramic"],
    "Bol à une anse": ["vessel_ceramic"],
    "Image pieuse": ["painting_drawing"],
    "Collier-amulette": ["jewelry", "amulet_ritual"],
    "Dents de félin : amulette": ["amulet_ritual"],
    "Amulette à 3 pointes": ["amulet_ritual"],
    "Amulette complexe": ["amulet_ritual"],
    "Talisman": ["amulet_ritual"],
    "Masque de diable": ["sculpture", "amulet_ritual"],
    "Disque": ["unclassified"],
    "Petit poignard": ["weapon"],
    'Figurine "à deux têtes" de type amulette': ["sculpture", "amulet_ritual"],
    "Assommoir à cochons": ["weapon"],
    "Serpentins": ["textile"],
    "Amulette pour la nourriture": ["amulet_ritual"],
    "Amulette en forme de bélier": ["amulet_ritual"],
    "Amulette en forme de brebis et de trois béliers": ["amulet_ritual"],
    "Filet de portage": ["textile"],
    "Effigie ancestrale": ["sculpture"],
    "Bol": ["vessel_ceramic"],
    "Flèches": ["weapon"],
    "Amulette ?": ["amulet_ritual"],
    "Massue de jet": ["weapon"],
    "Collier, couronne ou anneau de chapeau": ["jewelry"],
    "Elément cylindrique": ["unclassified"],
    "Moulin à sel": ["unclassified"],
    "Arme de pêche": ["weapon"],
    "Amulette de Kumanthong": ["amulet_ritual"],
    "Marmite": ["vessel_ceramic"],
    "Elément d'un modèle réduit de pagode": ["architectural_element"],
    "Bâton": ["unclassified"],
    "Volume tatoué": ["unclassified"],
    "Vue prise à Amboine dans le ravin de Batou-Ganton (Moluques)": [
        "painting_drawing"
    ],
}

_MUSEUM_MAPS: dict[str, dict[str, list[str]]] = {
    "met": MET_OBJECT_TYPE_MAP,
    "louvre": LOUVRE_OBJECT_TYPE_MAP,
    "bm": BM_OBJECT_TYPE_MAP,
    "qb": QUAIBRANLY_OBJECT_TYPE_MAP,
}


def classify_object_type(source_museum: str | None, object_name: str | None) -> list[str]:
    """Devuelve 1-3 tags del vocabulario cerrado para un `objectName` crudo.

    Lookup EXACTO (no keyword/substring) contra la tabla del museo
    correspondiente — a diferencia de `geocode.py`, `objectName` es un campo
    corto y ya bastante específico, sin el riesgo de falso positivo por
    substring que motivó `_keyword_matches()` para la geografía.

    Cae a `["unclassified"]` si `source_museum` no es uno de los 4 conocidos,
    si `object_name` es `None`/vacío, o si el valor no está todavía en la
    tabla (mismo criterio que el resto del pipeline: no inventar una
    clasificación que no verificamos a mano).
    """
    if not object_name:
        return list(_UNCLASSIFIED)
    table = _MUSEUM_MAPS.get((source_museum or "").strip().lower())
    if table is None:
        return list(_UNCLASSIFIED)
    tags = table.get(object_name.strip())
    if not tags:
        return list(_UNCLASSIFIED)
    return list(tags)
