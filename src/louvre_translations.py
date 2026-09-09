"""
Traducciones al ingles para la metadata cruda del Louvre (title/medium/creditLine).

Generado programaticamente (ronda del 09/09) a partir de los 198 titulos, 27
modos de creditLine y ~140 terminos comunes de medium -- ver CLAUDE.md, seccion
"Metadata cruda del Louvre traducida al ingles" para el detalle completo del
alcance y las decisiones de que se tradujo vs. que se dejo en frances a proposito.
"""

import re

TITLE_TRANSLATIONS: dict[str, str] = {'Aiguière': 'Ewer', 'Aiguière en cristal de roche du trésor de Saint-Denis': 'Rock crystal ewer from the Saint-Denis treasury', 'Aiguière à tête de coq': 'Ewer with a rooster-head spout', 'Akhénaton et Néfertiti': 'Akhenaten and Nefertiti', 'Antinous Mondragone': 'Antinous Mondragone', 'Aphrodite du type de la Vénus du Capitole': 'Aphrodite of the Capitoline Venus type', 'Aphrodite à la tortue': 'Aphrodite with a Tortoise', 'Apollon citharède': 'Apollo Citharoedus', 'Apollon de Piombino': 'Apollo of Piombino', 'Aquamanile fragmentaire en forme de bovidé': 'Fragmentary aquamanile in the shape of a bovine', 'Aquamanile zoomorphe': 'Zoomorphic aquamanile', 'Arès Borghèse': 'Borghese Ares', 'Athéna Mattéi': 'Athena Mattei', 'Autel de Domitius Ahenobarbus': 'Altar of Domitius Ahenobarbus', 'Bague aux chevaux': 'Ring with horses', 'Bassin dit "Baptistère de Saint Louis"': 'Basin known as the "Baptistère de Saint Louis"', 'Bol': 'Bowl', 'Bouteille aux animaux passant': 'Bottle with passing animals', "Buste d'Akhénaton": 'Bust of Akhenaten', 'Cadenas en forme de cheval': 'Padlock in the shape of a horse', 'Carreau de revêtement': 'Wall tile', 'Carreau hexagonal à inscription funéraire poétique': 'Hexagonal tile with a poetic funerary inscription', 'Chandelier aux canards': 'Candlestick with ducks', 'Chien de Sumuel': 'Dog of Sumu-El', 'Coffre à décor floral': 'Chest with floral decoration', 'Coffret': 'Small box (casket)', 'Coupe': 'Cup', 'Coupe au réseau végétal': 'Cup with vegetal scrollwork decoration', 'Coupe aux nuages "tchi"': 'Cup with "chi" cloud motifs', 'Coupe aux phénix en vol': 'Cup with flying phoenixes', "Coupe à décor d'arabesques": 'Cup with arabesque decoration', 'Coupe à décor épigraphique': 'Cup with epigraphic decoration', 'Coupelle': 'Small cup', 'Couteau du Gebel el-Arak': 'Gebel el-Arak Knife', 'Cratère Borghèse': 'Borghese Krater', "Dame d'Auxerre": 'Lady of Auxerre', 'Diane de Gabies': 'Diana of Gabii', 'Diane de Versailles': 'Diana of Versailles', 'Dinos du peintre de la gorgone': 'Dinos by the Gorgon Painter', 'Edicule rectangulaire': 'Rectangular naos (shrine)', 'Embout de fontaine et son boisseau': 'Fountain spout and its housing', 'Figurine du démon Pazuzu': 'Figurine of the demon Pazuzu', 'Fond de coupe': 'Base of a cup', 'Fond de coupe au cavalier': 'Base of a cup with a horseman', 'Frise des archers': 'Frieze of the Archers', 'Félin poids de tapis (?)': 'Feline-shaped carpet weight (?)', 'Gladiateur Borghèse': 'Borghese Gladiator', 'Globe céleste': 'Celestial globe', 'Gobelet aux joueurs de polo': 'Goblet with polo players', 'Grande coupe au cavalier': 'Large cup with a horseman', 'Grande coupe aux rinceaux verts': 'Large cup with green scrollwork', 'Hercule luttant contre le triple Géryon': 'Hercules fighting the triple-bodied Geryon', 'Hermaphrodite endormi': 'Sleeping Hermaphroditus', 'Ivoire d’Arslan Tash': 'Arslan Tash ivory', 'Ivoire d’Arslan Tash inscrit': 'Inscribed Arslan Tash ivory', 'Korè de Samos': 'Kore of Samos', 'Kouros de Paros': 'Kouros of Paros', 'Kudurru de Marduk-apla-iddina I': 'Kudurru of Marduk-apla-iddina I', 'Kudurru de Meli-Shipak': 'Kudurru of Meli-Shipak', 'Kudurru de Nazimaruttash': 'Kudurru of Nazi-Maruttash', 'Kudurru du roi Melishipak II': 'Kudurru of King Melishipak II', 'Kudurru du roi Melishipak II : enceinte et bateau': 'Kudurru of King Melishipak II: enclosure and boat', "L'Adorant de Larsa": 'The Worshipper of Larsa', 'Lampe à six becs': 'Lamp with six spouts', "Lance colossale inscrite au nom d'un roi de Kish": 'Colossal spearhead inscribed with the name of a king of Kish', "Le Christ et l'abbé Ména": 'Christ and Abbot Mena', 'Le passage des Théores - Apollon Nymphagète et les Nympes': 'The Theoric Procession — Apollo Nymphagetes and the Nymphs', 'Le passage des Théores - Hermès Agoraios': 'The Theoric Procession — Hermes Agoraios', 'Le passage des Théores - les Charites': 'The Theoric Procession — the Charites', 'Le scribe accroupi': 'The Seated Scribe', 'Les soldats prétoriens': 'The Praetorian Soldiers', "Linteau d'Imru' al-Qays": "Lintel of Imru' al-Qays", 'Lion de Mari': 'Lion of Mari', 'Lion dit "de Monzon"': 'Lion known as "the Monzón Lion"', "Mastaba d'Akhethétep": 'Mastaba of Akhethetep', 'Mosaïque du jugement de Pâris': 'Mosaic of the Judgment of Paris', 'Moule à estamper': 'Stamping mold', 'Métope du temple de Zeus à Olympie, Héraclès et le taureau de Crète': 'Metope from the Temple of Zeus at Olympia, Heracles and the Cretan Bull', 'Naos des décades': 'Naos of the Decades', 'Nu-banda Ebih-Il': 'Superintendent Ebih-Il', "Nécessaire d'orfèvre": "Goldsmith's tool kit", 'Obélisque de Manishtusu': 'Obelisk of Manishtusu', 'Palette au taureau': 'Palette with a bull', 'Palette aux quatre canidés': 'Palette with four canines', 'Pallas de Velletri': 'Pallas of Velletri', "Panneau droit d'une porte à deux vantaux à scènes de divertissement et thèmes animaliers": 'Right panel of a double door with entertainment scenes and animal motifs', 'Peinture de "l\'Investiture"': 'Painting of the "Investiture"', 'Plaque de revêtement à décor de lampe et à inscription coranique': "Revetment tile with a lamp motif and Qur'anic inscription", 'Plat aux capridés riant': 'Dish with laughing caprids', 'Plat tripode au cavalier ailé': 'Tripod dish with a winged horseman', 'Plat à décor rayonnant enfermant des branches fleuries': 'Dish with radiating decoration enclosing flowering branches', 'Plat à inscription rayonnante': 'Dish with radiating inscription', 'Plat à la grue en vol et nuages "tchi"': 'Dish with a flying crane and "chi" cloud motifs', 'Plateau tripode': 'Tripod tray', 'Poignard (khanjar) à tête de cheval': 'Dagger (khanjar) with a horse-head hilt', "Porche d'une demeure mamlouke au Caire (Qasr Rumi)": 'Porch of a Mamluk house in Cairo (Qasr Rumi)', "Portrait d'Homère": 'Portrait of Homer', 'Portrait de Ptolémée Ier': 'Portrait of Ptolemy I', "Portrait de l'empereur Jahangir tenant dans ses mains celui de son père, l'empereur Akbar (page d'album)": 'Portrait of Emperor Jahangir holding a portrait of his father, Emperor Akbar (album page)', 'Portrait en hermès d\'Alexandre, dit "Alexandre Azara"': 'Herm-portrait of Alexander, known as the "Azara Herm"', "Pyxide au nom d'al-Mughira": 'Pyxis in the name of al-Mughira', "Sarcophage d'Eshmunazor": 'Sarcophagus of Eshmunazor', 'Sarcophage de la Traditio Legis': 'Sarcophagus of the Traditio Legis', 'Sarcophage des époux': 'Sarcophagus of the Spouses', 'Sphinx de Tanis': 'Great Sphinx of Tanis', "Statue d'Amon et Toutânkhamon": 'Statue of Amun and Tutankhamun', "Statue d'Osorkon Ier": 'Statue of Osorkon I', 'Statue de Gudea dite "Petit Gudea assis"': 'Statue of Gudea known as the "Small Seated Gudea"', 'Statue de Gudea dite "au vase jaillissant"': 'Statue of Gudea known as "with the flowing vase"', 'Statue de Karomama': 'Statue of Karomama', 'Statue de Tiy et Amenhotep III': 'Statue of Tiye and Amenhotep III', 'Statue de la déesse Narundi': 'Statue of the goddess Narundi', 'Statue de la reine Napirasu': 'Statue of Queen Napirasu', 'Statue guérisseuse': 'Healing statue', "Stèle d'Imény": 'Stele of Imeny', 'Stèle de Bakhtan': 'Stele of Bakhtan (Bentresh Stele)', 'Stèle de Mesha': 'Mesha Stele', 'Stèle de Naram-Sin': 'Stele of Naram-Sin', 'Stèle de Shihan': 'Stele of Shihan', 'Stèle de Tapéret': 'Stele of Taperet', 'Stèle de Yehawmilk': 'Stele of Yehawmilk', 'Stèle de Zakkur': 'Stele of Zakkur', 'Stèle des vautours': 'Stele of the Vultures', 'Stèle du Baal au foudre': 'Stele of Baal with a Thunderbolt', 'Stèle du Bannissement': 'Stele of the Banishment', "Stèle frontière d'Akhénaton": 'Boundary stele of Akhenaten', 'Stèle funéraire de Si-Gabbor': 'Funerary stele of Si-Gabbor', "Stèle funéraire de l'exaltation de la fleur": 'Funerary stele of the "Exaltation of the Flower"', 'Suaire de Saint-Josse': 'Shroud of Saint-Josse', 'Sénèque mourant': 'Dying Seneca', 'Taharqa et Hémen': 'Taharqa and Hemen', 'Tapis "vase"': '"Vase" carpet', 'Tapis à décor de jardin de paradis, dit "de Mantes"': 'Carpet with a paradise-garden design, known as the "Mantes Carpet"', 'Tirage du "Galet d\'Antibes" ou "Galet de Terpon"': 'Cast of the "Antibes Pebble" or "Pebble of Terpon"', "Triade d'Osorkon": 'Triad of Osorkon', 'Triade divine': 'Divine triad', 'Tête de Djedefrê': 'Head of Djedefre', 'Tête de Mithridate VI Eupator': 'Head of Mithridates VI Eupator', 'Tête de cheval': 'Horse head', 'Tête de félin': 'Feline head', 'Tête royale dite "tête de Hammurabi"': 'Royal head known as the "Head of Hammurabi"', "Vantail de porte de sacristie faisant partie d'une paire": 'Sacristy door leaf, part of a pair', 'Vantail à décor de polygones': 'Door leaf with polygon decoration', 'Vase au nom du sultan d\'al-Malik al-Nasir, Salah al-Din Yusuf, dit "vase Barberini"': 'Vase in the name of Sultan al-Malik al-Nasir Salah al-Din Yusuf, known as the "Barberini Vase"', "Vase d'Enmetena": 'Vase of Enmetena', "Vase d'Ishtar": 'Vase of Ishtar', 'Vase en forme de joueur de tambourin': 'Vase in the shape of a tambourine player', 'Victoire de Samothrace': 'Winged Victory of Samothrace', "Vénus d'Arles": 'Venus of Arles', 'Vénus de Milo': 'Venus de Milo', 'Zodiaque de Dendéra': 'Zodiac of Dendera', 'amphore': 'amphora', 'amulette': 'amulet', 'arula': 'arula (small altar)', 'autel': 'altar', 'autel ; figurine': 'altar; figurine', 'calice': 'chalice', 'coupe': 'cup', "cratère d'Antée": 'krater of Antaeus', "cratère d'Eurytios": 'krater of Eurytios', 'cuiller à fard à la nageuse': 'cosmetic spoon with a swimmer', 'figurine': 'figurine', 'figurine ; enseigne divine': 'figurine; divine emblem', 'figurine ; statuette': 'figurine; statuette', 'figurine ; élément de meuble ; serrure': 'figurine; furniture element; lock', "figurine d'Osiris": 'figurine of Osiris', 'groupe statuaire représentant un couple en Mars et Vénus': 'statue group representing a couple as Mars and Venus', 'hache': 'axe', 'il Moro, le Maure': 'il Moro, the Moor', 'inscription': 'inscription', 'kudurru': 'kudurru', 'lécythe': 'lekythos', 'modèle': 'model', 'mors': 'bit (horse bit)', 'ostracon figuré': 'figured ostracon', 'papyrus Jumilhac': 'Jumilhac Papyrus', 'parchemin': 'parchment', 'pendeloque': 'pendant', 'poignard ; fourreau': 'dagger; sheath', 'pyramidion': 'pyramidion', 'relief mithriaque': 'Mithraic relief', 'relief mural': 'wall relief', 'stamnos': 'stamnos', 'statue': 'statue', 'statue cube': 'cube statue (block statue)', 'statue de Marcellus': 'Statue of Marcellus', 'statue de couple': 'statue of a couple', 'statue de pleureuse': 'statue of a mourner', 'statuette': 'statuette', 'statuette ; ex-voto': 'statuette; votive offering', 'stèle cintrée': 'arched stele', 'tablette': 'tablet', 'tiare de Saitapharnes': 'Tiara of Saitaphernes', 'vase': 'vase', 'vase de Sosibios': 'Vase of Sosibios', 'Étoile à six branches au personnage assis': 'Six-pointed star with a seated figure', 'élément architectural': 'architectural element', 'élément de mobilier': 'furniture element'}

CREDIT_LINE_MODE_TRANSLATIONS: dict[str, str] = {'achat': 'purchase', 'don': 'gift', 'partage après fouilles': 'division of finds after excavation (partage)', 'legs': 'bequest', 'affecté au Louvre': 'allocated to the Louvre', 'achat en vente publique': 'purchase at public auction', 'acquisition en mission': 'acquired during a mission', 'don après fouilles': 'gift after excavation', 'saisie révolutionnaire': 'revolutionary seizure', 'donation': 'donation', 'achat et don': 'purchase and gift', 'saisie napoléonienne': 'Napoleonic seizure', 'don manuel': 'hand-delivered gift', "donation sous réserve d'usufruit": 'donation subject to usufruct', 'versement': 'transfer', 'entrée après fouilles': 'entry after excavation', "legs sous réserve d'usufruit": 'bequest subject to usufruct', 'saisie': 'seizure', 'entrée au Louvre avant': 'entered the Louvre before', 'affectation, attribution': 'allocation, attribution', 'ancien fonds': 'pre-existing holdings', 'échange': 'exchange', 'achat après arrêt en douane': 'purchase after customs seizure', 'dation': 'dation in lieu of tax payment', 'entrée - Collection de Louis XIV': 'entry — Collection of Louis XIV', "mode d'acquisition inconnu": 'acquisition method unknown', 'achat avec participation des Amis du Louvre': 'purchase with contribution from the Amis du Louvre'}

MEDIUM_PREFIX_TRANSLATIONS: dict[str, str] = {'Matériau': 'Material', 'Technique': 'Technique', 'Matériau/Technique': 'Material/Technique', 'Matériau secondaire': 'Secondary material', 'Couleur': 'Color', 'Précision technique': 'Technical detail'}

MEDIUM_TERM_TRANSLATIONS: dict[str, str] = {'ronde-bosse': 'sculpture in the round', 'céramique': 'ceramic', 'calcaire': 'limestone', 'peinture': 'paint', 'bas-relief': 'bas-relief', 'bronze': 'bronze', 'marbre': 'marble', 'argile': 'clay', 'or': 'gold', 'gravé': 'engraved', 'bois': 'wood', 'marbre de paros': 'Parian marble', 'haut-relief': 'high relief', 'peinture brillante': 'glossy paint', 'incrustation': 'inlay', 'cuivre': 'copper', 'incisé = incision': 'incised = incision', 'ivoire': 'ivory', 'basalte': 'basalt', 'terre cuite': 'terracotta', 'bas-relief saillant': 'raised bas-relief', 'bas-relief creux = sculpture en creux': 'sunk relief = incised relief', 'rehaut rouge': 'red highlight', 'pierre': 'stone', 'argent': 'silver', 'modelé': 'modeled', 'dessin au trait': 'line drawing', 'figures noires': 'black-figure', 'trépan': 'drill', 'alliage cuivreux': 'copper alloy', 'diorite': 'diorite', 'gravure': 'engraving', 'albâtre': 'alabaster', 'gravé = gravure': 'engraved = engraving', 'rehaut blanc': 'white highlight', 'marbre du pentélique': 'Pentelic marble', 'laiton': 'brass', 'métal  coulé': 'cast metal', 'métal coulé': 'cast metal', 'stéatite': 'steatite', 'grès': 'sandstone', 'coulé fondu': 'cast/molten', 'métal': 'metal', 'métal  martelé': 'hammered metal', 'métal martelé': 'hammered metal', 'décor peint sur engobe sous glaçure transparente': 'decoration painted on slip under transparent glaze', 'composite': 'composite', 'albâtre égyptien': 'Egyptian alabaster (calcite)', 'granite rose': 'pink granite', 'grauwacke': 'greywacke', 'grès silicifié': 'silicified sandstone', 'rouge': 'red', 'stucage': 'stuccoing', 'gabbro': 'gabbro', 'polychromie': 'polychromy', 'doré': 'gilded', 'incisé': 'incised', 'moulé': 'molded', 'figures rouges': 'red-figure', 'plomb': 'lead', 'décor repoussé': 'repoussé decoration', 'décor peint sous glaçure transparente colorée': 'decoration painted under colored transparent glaze', 'décor ciselé': 'chiseled decoration', 'champlevé': 'champlevé', 'décor peint sur glaçure opacifiée': 'decoration painted on opacified glaze', 'textile': 'textile', 'martelage': 'hammering', 'vert': 'green', 'bitume': 'bitumen', 'noir': 'black', 'perséa': 'persea wood', 'cristal de roche': 'rock crystal', 'faïence siliceuse': 'siliceous faience', "ivoire d'éléphant": 'elephant ivory', 'encre': 'ink', 'incrusté': 'inlaid', 'martelé': 'hammered', 'fer': 'iron', 'sculpté': 'carved', 'peint': 'painted', 'verre': 'glass', 'os': 'bone', 'fonte en creux': 'hollow casting', 'incrustation = incrusté': 'inlay = inlaid', 'engobe': 'slip', 'marbre noir': 'black marble', 'marbre )': 'marble', 'décor ajouré': 'openwork decoration', 'décor gravé': 'engraved decoration', 'décor de lustre métallique sur glaçure transparente': 'metallic luster decoration on transparent glaze', 'rehauts de couleur': 'color highlights', 'décor sculpté': 'carved decoration', 'décor peint': 'painted decoration', 'poil : laine': 'hair: wool', 'noeud asymétrique': 'asymmetric knot', 'décor moulé sous glaçure opacifiée colorée': 'molded decoration under colored opacified glaze', 'jade': 'jade', 'chloritite': 'chloritite', 'placage': 'veneer', 'glaçurage': 'glazing', 'papyrus': 'papyrus', 'blanc-noir': 'white-black', 'fonte creuse': 'hollow casting', 'faibles tracés de couleur ocre jaune et rouge': 'faint traces of yellow and red ochre', "grenadille d'afrique": 'African blackwood (grenadilla)', 'lapis-lazuli': 'lapis lazuli', 'blanc-noir-rouge-bleu': 'white-black-red-blue', 'dorure': 'gilding', 'bleu vif': 'bright blue', 'rouge-traces': 'red — traces', "ivoire d'hippopotame": 'hippopotamus ivory', 'silex': 'flint', 'dessin': 'drawing', 'ocre jaune-rouge-noir': 'yellow-red-black ochre', 'lignes repère': 'guide lines', 'rouge-blanc-bleu-noir': 'red-white-blue-black', 'ocre jaune-rouge-bleu turquoise-bleu': 'yellow ochre-red-turquoise blue-blue', 'granodiorite': 'granodiorite', 'acacia': 'acacia wood', 'obsidienne': 'obsidian', 'rouge-noir-jaune': 'red-black-yellow', 'cornaline': 'carnelian', 'grenetis': 'beaded wire (grenetis)', 'incrustation cloisonnée': 'cloisonné inlay', 'tamaris': 'tamarisk wood', 'vernis': 'varnish', 'blanc-vert-rouge-bleu-rose': 'white-green-red-blue-pink', 'rouge-noir': 'red-black', 'jaune': 'yellow', 'tissu stuqué': 'stuccoed fabric', 'parchemin': 'parchment', 'écriture': 'writing', 'figuier sycomore': 'sycamore fig wood', "peinture à l'encaustique": 'encaustic painting', 'peinture à la détrempe': 'tempera painting', 'dolérite': 'dolerite', 'bas-relief champlevé': 'champlevé bas-relief', 'quartzite ")': 'quartzite', 'coquillage = coquille': 'shell = shell', 'lapis lazuli': 'lapis lazuli', 'riveté': 'riveted', 'plaqué': 'plated', 'calcaire oolithique': 'oolitic limestone', 'céramique siliceuse à glaçure': 'glazed siliceous ceramic', "intérieur de l'embouchure peint en noir": 'interior of the mouth painted black', 'marbre de lartos': 'Lartos marble', 'taillé': 'carved', 'pigments blancs : carbonate et sulfate de calcium ; jaune : jarosite et natrojarosite ; bruns et ocres : terres ferrugineuses ; orangé : minium ; vert : pas de malachite': 'white pigments: calcium carbonate and sulfate; yellow: jarosite and natrojarosite; browns and ochres: ferruginous earths; orange: minium (lead oxide); green: no malachite detected', 'contient un peu de cuivre et de plomb': 'contains a small amount of copper and lead', 'filigranes': 'filigree', 'filigrané = filigrane': 'filigreed = filigree'}



def translate_title(title: str | None) -> str | None:
    """Traduccion directa via diccionario -- las 198 piezas del Louvre estan
    cubiertas. Si aparece un titulo nuevo (pieza nueva sumada al pipeline),
    devuelve el texto original en frances sin traducir (fallback seguro, el
    frontend ya cae de vuelta al campo base si falta el _en)."""
    if not title:
        return None
    return TITLE_TRANSLATIONS.get(title, title)


def translate_credit_line(credit_line: str | None) -> str | None:
    """El creditLine se armo en build_row() como "{mode} ({date})" -- se separa
    la fecha entre parentesis (se preserva tal cual, no es texto a traducir)
    y se traduce solo el modo via el diccionario cerrado de 27 valores."""
    if not credit_line:
        return None
    s = credit_line.strip()
    m = re.match(r"^(.*?)(\s*\([^)]*\))\s*$", s)
    if m:
        mode_part = m.group(1).strip()
        date_part = " " + m.group(2).strip()
    else:
        mode_part = s
        date_part = ""
    translated_mode = CREDIT_LINE_MODE_TRANSLATIONS.get(mode_part, mode_part)
    return f"{translated_mode}{date_part}"


def _split_top_level_commas(text: str) -> list[str]:
    """Separa por comas, pero no dentro de parentesis (para no partir un
    termino con su calificador parentetico, ej. "grenadille d'afrique
    (bois)")."""
    parts = []
    depth = 0
    current = ""
    for ch in text:
        if ch == "(":
            depth += 1
            current += ch
        elif ch == ")":
            depth = max(0, depth - 1)
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current:
        parts.append(current)
    return parts


def _translate_single_term(term: str) -> str:
    """Traduce un termino via el glosario, preservando su calificador
    parentetico sin traducir (ej. "marbre (blanc)" -> "marble (blanc)" si
    "blanc" dentro del parentesis no esta en el glosario -- se prioriza no
    inventar sobre cobertura total). Si el termino base no esta en el
    glosario, se deja la linea entera tal cual en frances -- mismo criterio
    del proyecto de no forzar traduccion sin confianza real."""
    term = term.strip()
    if not term:
        return term
    m = re.match(r"^(.*?)(\s*\([^)]*\))?$", term)
    base = (m.group(1) or "").strip()
    paren = m.group(2) or ""
    key = base.lower()
    if key in MEDIUM_TERM_TRANSLATIONS:
        return f"{MEDIUM_TERM_TRANSLATIONS[key]}{paren}"
    return term


def translate_medium(medium: str | None) -> str | None:
    """Traduce el campo medium linea por linea. Cada linea puede tener un
    prefijo tipo "Matériau: ..." (traducido via MEDIUM_PREFIX_TRANSLATIONS)
    seguido de terminos separados por coma (traducidos via
    MEDIUM_TERM_TRANSLATIONS cuando estan en el glosario). Los terminos que
    no estan en el glosario -- texto libre/descriptivo mas largo, analisis de
    pigmentos, notas de condicion puntuales -- se dejan sin traducir en
    frances a proposito: cubre los ~140 terminos comunes de
    materiales/tecnicas/colores que concentran la gran mayoria de las
    ocurrencias, sin arriesgar una traduccion apurada e incorrecta del resto.
    Ver CLAUDE.md para el detalle de esta decision de cobertura parcial."""
    if not medium:
        return None
    out_lines = []
    for line in medium.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            prefix, rest = line.split(":", 1)
            prefix = prefix.strip()
            rest = rest.strip()
            translated_prefix = MEDIUM_PREFIX_TRANSLATIONS.get(prefix, prefix)
            parts = _split_top_level_commas(rest)
            translated_rest = ", ".join(_translate_single_term(p) for p in parts)
            out_lines.append(f"{translated_prefix}: {translated_rest}")
        else:
            parts = _split_top_level_commas(line)
            out_lines.append(", ".join(_translate_single_term(p) for p in parts))
    return "\n".join(out_lines)
