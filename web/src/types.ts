export interface ProvenanceEvent {
  event_order: number | null;
  event_type: string | null;
  event_date: string | null;
  actor_or_institution: string | null;
  location: string | null;
  description: string | null;
  source_url: string | null;
  source_type: string | null;
  confidence_level: string | null;
}

export interface ObjectContext {
  research_status: string;
  context_flags: string[];
  associated_communities_or_states: string | null;
  notes: string | null;
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
  originPrecision: string | null;
  originLat: number;
  originLon: number;
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
