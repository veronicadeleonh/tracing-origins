export interface ProvenanceEvent {
  event_order: number | null;
  event_type: string | null;
  event_date: string | null;
  actor_or_institution: string | null;
  location: string | null;
  description: string | null;
  // Traducciones agregadas el 17/08 (toggle ES/EN ampliado a layer 3, ver
  // CLAUDE.md). descriptionEs siempre viene poblado (es el `description`
  // original para las piezas del Louvre/BM, o su traducción para las del
  // Met); descriptionEn es la contraparte en inglés. `description` se deja
  // sin tocar por compatibilidad, pero la UI debería usar descriptionEs/En.
  descriptionEs: string | null;
  descriptionEn: string | null;
  source_url: string | null;
  source_type: string | null;
  confidence_level: string | null;
}

export interface ObjectContext {
  research_status: string;
  context_flags: string[];
  associated_communities_or_states: string | null;
  notes: string | null;
  notesEn: string | null;
}

export interface MuseumObject {
  objectID: string;
  sourceMuseum: string | null;
  title: string | null;
  objectName: string | null;
  department: string | null;
  culture: string | null;
  period: string | null;
  dynasty: string | null;
  objectDate: string | null;
  medium: string | null;
  creditLine: string | null;
  accessionYear: string | null;
  excavation: string | null;
  country: string | null;
  region: string | null;
  subregion: string | null;
  primaryImage: string | null;
  objectURL: string | null;
  originLabel: string | null;
  originLabelEn: string | null;
  originPrecision: string | null;
  originLat: number;
  originLon: number;
  // País moderno de origen (19/08, búsqueda "al revés" por país) — separado
  // de originLabel a propósito: originLabel puede ser un sitio puntual
  // ("Nimrud") o una región histórica ("Luristán"), originCountry es
  // siempre un país moderno reconocible, o null en el puñado de casos
  // donde el origen es demasiado difuso para asignarle uno solo (ver
  // geocode.py, KEYWORD_COUNTRY).
  originCountry: string | null;
  originCountryEn: string | null;
  context: ObjectContext | null;
  events: ProvenanceEvent[];
}

export interface MuseumDestination {
  lat: number;
  lon: number;
  name: string;
  city: string;
}

export interface DataBundle {
  museums: Record<string, MuseumDestination>;
  objects: MuseumObject[];
}
