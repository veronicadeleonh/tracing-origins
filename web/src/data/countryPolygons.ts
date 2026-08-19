// Búsqueda por país vía click en el mapa (19/08, segunda vuelta a pedido de
// la usuaria — la primera vuelta fue solo un buscador de texto, ver
// CLAUDE.md). `countries.geojson` (web/public/, Natural Earth 110m admin-0,
// dominio público, 178 features) se usa como capa invisible de hit-testing
// para saber en qué país cayó un click; sus nombres (`properties.name`,
// inglés, a veces en forma abreviada tipo "Dem. Rep. Congo") no coinciden
// textualmente con nuestro `originCountry`/`originCountryEn` (traducidos a
// mano, formas completas) — esta tabla traduce de uno a otro. Solo cubre los
// ~79 países que efectivamente aparecen en nuestros datos; países sin
// piezas en la muestra no necesitan entrada (un click ahí no encuentra
// ningún CountryGroup y no pasa nada, ver App.tsx).
//
// "North Korea"/"South Korea" -> mismo país nuestro ("Corea"): nuestro dato
// no distingue cuál de las dos, viene de CULTURE_KEYWORDS del Met
// ("Korea", ambiguo) — clickear cualquiera de las dos abre el mismo grupo.
//
// Natural Earth a 110m de resolución no incluye Tonga (islas demasiado
// chicas para esa resolución) — se agregó a mano un rectángulo de
// hit-testing alrededor de sus coordenadas (ver countries.geojson) para no
// dejar ese país sin clickear; no pretende ser un contorno cartográfico
// real, solo un área clickeable.
export const NATURAL_EARTH_NAME_TO_COUNTRY_KEY: Record<string, string> = {
  "Afghanistan": "Afganistán",
  "Algeria": "Argelia",
  "Australia": "Australia",
  "Bangladesh": "Bangladés",
  "Bolivia": "Bolivia",
  "Botswana": "Botsuana",
  "Brazil": "Brasil",
  "Cambodia": "Camboya",
  "Cameroon": "Camerún",
  "Canada": "Canadá",
  "Chile": "Chile",
  "China": "China",
  "Colombia": "Colombia",
  "Cyprus": "Chipre",
  "Côte d'Ivoire": "Costa de Marfil",
  "Dem. Rep. Congo": "República Democrática del Congo",
  "Ecuador": "Ecuador",
  "Egypt": "Egipto",
  "Ethiopia": "Etiopía",
  "Fiji": "Fiyi",
  "France": "Francia",
  "Ghana": "Ghana",
  "Greece": "Grecia",
  "Guatemala": "Guatemala",
  "Guyana": "Guyana",
  "India": "India",
  "Indonesia": "Indonesia",
  "Iran": "Irán",
  "Iraq": "Irak",
  "Israel": "Israel",
  "Italy": "Italia",
  "Jamaica": "Jamaica",
  "Japan": "Japón",
  "Jordan": "Jordania",
  "Kenya": "Kenia",
  "Lebanon": "Líbano",
  "Madagascar": "Madagascar",
  "Malawi": "Malaui",
  "Mali": "Malí",
  "Mexico": "México",
  "Mongolia": "Mongolia",
  "Morocco": "Marruecos",
  "Myanmar": "Birmania (Myanmar)",
  "Namibia": "Namibia",
  "Nepal": "Nepal",
  "New Zealand": "Nueva Zelanda",
  "Nigeria": "Nigeria",
  "North Korea": "Corea",
  "Pakistan": "Pakistán",
  "Palestine": "Palestina",
  "Papua New Guinea": "Papúa Nueva Guinea",
  "Peru": "Perú",
  "Senegal": "Senegal",
  "Sierra Leone": "Sierra Leona",
  "Solomon Is.": "Islas Salomón",
  "South Africa": "Sudáfrica",
  "South Korea": "Corea",
  "Spain": "España",
  "Sri Lanka": "Sri Lanka",
  "Sudan": "Sudán",
  "Syria": "Siria",
  "Tajikistan": "Tayikistán",
  "Tanzania": "Tanzania",
  "Thailand": "Tailandia",
  "Tonga": "Tonga",
  "Trinidad and Tobago": "Trinidad y Tobago",
  "Tunisia": "Túnez",
  "Turkey": "Turquía",
  "Turkmenistan": "Turkmenistán",
  "Uganda": "Uganda",
  "Ukraine": "Ucrania",
  "United Kingdom": "Reino Unido",
  "United States of America": "Estados Unidos",
  "Uzbekistan": "Uzbekistán",
  "Vanuatu": "Vanuatu",
  "Venezuela": "Venezuela",
  "Vietnam": "Vietnam",
  "Yemen": "Yemen",
  "Zambia": "Zambia",
  "Zimbabwe": "Zimbabue",
};
