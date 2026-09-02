'use client';

import {
  ChevronRight,
  CircleAlert,
  ExternalLink,
  FileText,
  Focus,
  GitBranch,
  Hand,
  Map as MapIcon,
  Maximize2,
  Minus,
  Move,
  Pause,
  Play,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import { feature } from 'topojson-client';
import { geoGraticule10, geoNaturalEarth1, geoPath } from 'd3-geo';
import {
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select';

type Person = {
  individual_id: string;
  name: string;
  sex: string;
  birth: string;
  death: string;
  local_ids: string;
  source_refs: string;
  notes: string;
  family_as_child: string;
  families_as_spouse: string;
};

type Family = {
  family_id: string;
  husband_id: string;
  wife_id: string;
  children_ids: string;
  notes: string;
  source_refs: string;
};

type Source = {
  source_id: string;
  title: string;
  author: string;
  date: string;
  notes: string;
  origin: string;
};

type TreeData = {
  metadata: { title: string; updated: string; privacy: string; scope: string };
  people: Person[];
  families: Family[];
  sources: Source[];
};

type MapLocation = {
  location_id: string;
  label: string;
  latitude: number | null;
  longitude: number | null;
  precision: string;
};

type MapEvent = {
  event_id: string;
  person_id: string;
  person_name: string;
  event_type: string;
  date_text: string;
  year_min: number | null;
  year_max: number | null;
  location_id: string;
  side: 'Maternal' | 'Paternal';
  branch: string;
  confidence: string;
};

type MovementRecord = {
  movement_id: string;
  movement_type: 'intergenerational' | 'lifetime';
  person_id: string;
  from_location_id: string;
  to_location_id: string;
  year_min: number | null;
  side: 'Maternal' | 'Paternal';
};

type MigrationData = {
  metadata: {
    year_extent: [number, number];
    counts: { locations: number; events: number; movements: number; people_represented: number };
    movement_note: string;
    privacy_excluded_people: number;
  };
  locations: MapLocation[];
  events: MapEvent[];
  movements: MovementRecord[];
};

type LayoutNode = Person & { x: number; y: number; generation: number };
type RelationIndex = {
  parents: Map<string, string[]>;
  children: Map<string, string[]>;
  spouses: Map<string, string[]>;
  parentLinks: { parent: string; child: string }[];
  spouseLinks: { left: string; right: string }[];
};

const RECORD_FILES = [
  '1648-06-15_deborah-hopkins_birth-register.jpg',
  '1667-02-05_ephraim-doane_mary-knowles_marriage-register.jpg',
  '1682-02-04_joshua-cook_birth-register.jpg',
  '1682-04_patience-doane_birth-register.jpg',
  '1696_joshua-lane_birth-record.jpg',
  '1717_joshua-lane_bathsheba-robie_marriage-record.jpg',
  '1718_samuel-lane_birth-record.jpg',
  '1722_mary-james_birth-record.jpg',
  '1741-12-24_samuel-lane_mary-james_marriage.jpg',
  '1748-02-09_joshua-lane_nh-birth.jpg',
  '1769-11-15_joshua-lane_hannah-tilton_marriage.jpg',
  '1771-12-08_stephen-lane_nh-birth.jpg',
  '1774-02-26_levi-cook_birth-register.jpg',
  '1779-01-07_betsey-brown_birth-register.jpg',
  '1794-07-24_levi-cook_betsey-brown_marriage-register.jpg',
  '1797-06-05_stephen-lane_lois-currier_marriage.jpg',
  '1807-02-03_mary-lane_nh-birth-card.jpg',
  '1840-09-16_stephen-lane_will.jpg',
  '1841-05-05_stephen-lane_probate-letters.jpg',
  '1846-10-30_levi-cook_will_genesee.jpg',
  '1862_peter-william-mcnaughton_civil-war-town-register.jpg',
  '1868_relief-mcnaughton_dependent-pension-numerical-index.jpg',
  '1882-08-21_henry-vollmer_arrival-main.jpg',
  '1882-08-21_vollmer-family_arrival-main_page-0289.jpg',
  '1883-08-12_themes-pepper_anna-stelling_marriage-certificate.pdf',
  '1884-03-14_female-pepper_birth-certificate.pdf',
  '1892_henry-vollmer_ny-state-census.jpg',
  '1896_mary-a-mcnaughton_widow-pension-index.jpg',
  '1901_mayflower-descendant-vol3_john-doane-will.pdf',
  '1904_mayflower-descendant-vol6_eastham-vital-records.pdf',
  '1905-08-05_henry-jj-vollmer_marriage-certificate.pdf',
  '1910_frederick-carrie-doris-andrew-marsh_us-census.jpg',
  '1910_henry-madie-charles-vollmer_us-census.jpg',
  '1917-03-10_frederick-g-vollmer_death-certificate.pdf',
  '1918_henry-john-joseph-volmer_wwi-draft-card.jpg',
  '1919-01-03_madie-vollmer_death-certificate.pdf',
  '1919-12-17_mary-mcnaughton_ny-death-index.jpg',
  '1940-10-16_charles-frederick-vollmer_wwii-draft-card.jpg',
  '1940_charles-doris-henry-vollmer_us-census.jpg',
  'giles-hopkins_17th-century-records_pilgrim-hall.pdf',
  'plymouth-colony-records-vol1_1639-marriage.pdf',
  'relief-mcnaughton_mother-pension-index.jpg',
];

const ROOT_ID = 'I001';
const CARD_W = 174;
const CARD_H = 52;

const splitRefs = (value = '') => value.split(/[;,]/).map((part) => part.trim()).filter(Boolean);
const normalize = (value: string) => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
const confidenceFromNotes = (notes: string) => notes.match(/Confidence\s+([A-C])\s*\(([^)]+)\)/i)?.slice(1) ?? ['', 'Unrated'];
const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
const lifeYears = (person: Person) => {
  const birth = person.birth.match(/\b(1[4-9]\d{2}|20\d{2})\b/)?.[1];
  const death = person.death.match(/\b(1[4-9]\d{2}|20\d{2})\b/)?.[1];
  if (!birth && !death) return person.notes.toLowerCase().includes('living') ? 'Living' : 'Dates unknown';
  return `${birth ?? '?'}–${death ?? ''}`;
};
const cleanTitle = (filename: string) => filename.replace(/\.(jpg|pdf)$/i, '').replace(/^\d{4}(?:-\d{2}-\d{2})?_?/, '').replace(/_/g, ' ').replace(/-/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

function buildRelations(data: TreeData): RelationIndex {
  const parents = new Map<string, string[]>();
  const children = new Map<string, string[]>();
  const spouses = new Map<string, string[]>();
  const parentLinks: RelationIndex['parentLinks'] = [];
  const spouseLinks: RelationIndex['spouseLinks'] = [];

  const push = (map: Map<string, string[]>, key: string, value: string) => {
    if (!key || !value) return;
    const values = map.get(key) ?? [];
    if (!values.includes(value)) values.push(value);
    map.set(key, values);
  };

  data.families.forEach((family) => {
    const parentIds = [family.husband_id, family.wife_id].filter(Boolean);
    const childIds = splitRefs(family.children_ids);
    childIds.forEach((child) => parentIds.forEach((parent) => {
      push(parents, child, parent);
      push(children, parent, child);
      parentLinks.push({ parent, child });
    }));
    if (family.husband_id && family.wife_id) {
      push(spouses, family.husband_id, family.wife_id);
      push(spouses, family.wife_id, family.husband_id);
      spouseLinks.push({ left: family.husband_id, right: family.wife_id });
    }
  });
  return { parents, children, spouses, parentLinks, spouseLinks };
}

function buildLayout(data: TreeData, relations: RelationIndex) {
  const generation = new Map<string, number>([[ROOT_ID, 0]]);
  for (let pass = 0; pass < 80; pass += 1) {
    let changed = false;
    data.families.forEach((family) => {
      const adults = [family.husband_id, family.wife_id].filter(Boolean);
      const kids = splitRefs(family.children_ids);
      const knownAdult = adults.map((id) => generation.get(id)).find((value) => value !== undefined);
      const knownKid = kids.map((id) => generation.get(id)).find((value) => value !== undefined);
      if (knownAdult !== undefined) {
        adults.forEach((id) => { if (!generation.has(id)) { generation.set(id, knownAdult); changed = true; } });
        kids.forEach((id) => { if (!generation.has(id)) { generation.set(id, knownAdult + 1); changed = true; } });
      } else if (knownKid !== undefined) {
        adults.forEach((id) => { if (!generation.has(id)) { generation.set(id, knownKid - 1); changed = true; } });
      }
    });
    if (!changed) break;
  }

  const fallback = Math.max(...generation.values(), 0) + 1;
  data.people.forEach((person) => { if (!generation.has(person.individual_id)) generation.set(person.individual_id, fallback); });
  const groups = new Map<number, Person[]>();
  data.people.forEach((person) => {
    const gen = generation.get(person.individual_id) ?? fallback;
    groups.set(gen, [...(groups.get(gen) ?? []), person]);
  });
  groups.forEach((group) => group.sort((a, b) => a.name.localeCompare(b.name)));
  const levels = [...groups.keys()].sort((a, b) => a - b);
  const widest = Math.max(...[...groups.values()].map((group) => group.length));
  const width = Math.max(1500, widest * 194 + 240);
  const minGen = Math.min(...levels);
  const nodes: LayoutNode[] = [];
  levels.forEach((gen) => {
    const group = groups.get(gen) ?? [];
    const span = group.length * 194;
    const start = (width - span) / 2;
    group.forEach((person, index) => nodes.push({
      ...person,
      x: start + index * 194 + 10,
      y: (gen - minGen) * 112 + 44,
      generation: gen,
    }));
  });
  return { nodes, width, height: (levels.length - 1) * 112 + 160, generations: levels.length };
}

function collectLineage(selectedId: string, relations: RelationIndex) {
  const all = new Set<string>([selectedId]);
  const ancestors = new Set<string>();
  const descendants = new Set<string>();
  const walk = (id: string, index: Map<string, string[]>, result: Set<string>) => {
    (index.get(id) ?? []).forEach((next) => {
      if (result.has(next)) return;
      result.add(next);
      all.add(next);
      walk(next, index, result);
    });
  };
  walk(selectedId, relations.parents, ancestors);
  walk(selectedId, relations.children, descendants);
  return { all, ancestors, descendants };
}

function matchedRecords(person: Person) {
  const tokens = normalize(person.name).split(' ').filter((token) => token.length >= 4 && !['living', 'unknown'].includes(token));
  const surname = tokens.at(-1) ?? '';
  return RECORD_FILES.filter((filename) => {
    const fileTokens = normalize(filename).split(' ');
    const matched = tokens.filter((token) => fileTokens.some((fileToken) => fileToken.slice(0, 4) === token.slice(0, 4)));
    return matched.length >= 2 || (surname.length >= 5 && matched.includes(surname) && tokens.length === 1);
  });
}

function LoadingView() {
  return (
    <main className="loading-view">
      <div className="brand-mark"><Sparkles size={17} /></div>
      <p className="eyebrow">The Vollmer family archive</p>
      <h1>Opening the family tree…</h1>
    </main>
  );
}

function TreeCanvas({
  data,
  relations,
  selectedId,
  onSelect,
}: {
  data: TreeData;
  relations: RelationIndex;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const stageRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 0.72 });
  const [positioned, setPositioned] = useState(false);
  const layout = useMemo(() => buildLayout(data, relations), [data, relations]);
  const nodeMap = useMemo(() => new Map(layout.nodes.map((node) => [node.individual_id, node])), [layout.nodes]);
  const lineage = useMemo(() => collectLineage(selectedId, relations), [selectedId, relations]);

  const centerOn = (id: string, scale = transform.scale) => {
    const stage = stageRef.current;
    const node = nodeMap.get(id);
    if (!stage || !node) return;
    setTransform({
      x: stage.clientWidth / 2 - (node.x + CARD_W / 2) * scale,
      y: stage.clientHeight / 2 - (node.y + CARD_H / 2) * scale,
      scale,
    });
  };

  useEffect(() => {
    if (positioned || !stageRef.current) return;
    centerOn(ROOT_ID, 0.78);
    setPositioned(true);
  }, [positioned]);

  const zoom = (factor: number) => {
    const stage = stageRef.current;
    if (!stage) return;
    const next = Math.max(0.22, Math.min(2.2, transform.scale * factor));
    const cx = stage.clientWidth / 2;
    const cy = stage.clientHeight / 2;
    const worldX = (cx - transform.x) / transform.scale;
    const worldY = (cy - transform.y) / transform.scale;
    setTransform({ x: cx - worldX * next, y: cy - worldY * next, scale: next });
  };

  const wheel = (event: ReactWheelEvent) => {
    event.preventDefault();
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect) return;
    const px = event.clientX - rect.left;
    const py = event.clientY - rect.top;
    const next = Math.max(0.22, Math.min(2.2, transform.scale * (event.deltaY < 0 ? 1.1 : 0.9)));
    const wx = (px - transform.x) / transform.scale;
    const wy = (py - transform.y) / transform.scale;
    setTransform({ x: px - wx * next, y: py - wy * next, scale: next });
  };

  const pointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if ((event.target as Element).closest('[data-person-node]')) return;
    dragRef.current = { x: event.clientX, y: event.clientY, tx: transform.x, ty: transform.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const pointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    setTransform((current) => ({ ...current, x: drag.tx + event.clientX - drag.x, y: drag.ty + event.clientY - drag.y }));
  };

  return (
    <div
      ref={stageRef}
      className="tree-stage"
      onWheel={wheel}
      onPointerDown={pointerDown}
      onPointerMove={pointerMove}
      onPointerUp={() => { dragRef.current = null; }}
      onPointerCancel={() => { dragRef.current = null; }}
    >
      <svg width="100%" height="100%" role="tree" aria-label="Interactive family tree">
        <g transform={`translate(${transform.x} ${transform.y}) scale(${transform.scale})`}>
          {relations.parentLinks.map((link) => {
            const parent = nodeMap.get(link.parent);
            const child = nodeMap.get(link.child);
            if (!parent || !child) return null;
            const active = lineage.all.has(link.parent) && lineage.all.has(link.child);
            const x1 = parent.x + CARD_W / 2;
            const y1 = parent.y + CARD_H;
            const x2 = child.x + CARD_W / 2;
            const y2 = child.y;
            const mid = (y1 + y2) / 2;
            return <path key={`${link.parent}-${link.child}`} className={`tree-link ${active ? 'active' : ''}`} d={`M${x1} ${y1} V${mid} H${x2} V${y2}`} />;
          })}
          {relations.spouseLinks.map((link) => {
            const left = nodeMap.get(link.left);
            const right = nodeMap.get(link.right);
            if (!left || !right || left.generation !== right.generation) return null;
            const active = lineage.all.has(link.left) && lineage.all.has(link.right);
            return <path key={`${link.left}-${link.right}`} className={`spouse-link ${active ? 'active' : ''}`} d={`M${left.x + CARD_W} ${left.y + CARD_H / 2} H${right.x} `} />;
          })}
          {layout.nodes.map((node) => {
            const selected = node.individual_id === selectedId;
            const inLineage = lineage.all.has(node.individual_id);
            const [, confidenceLabel] = confidenceFromNotes(node.notes);
            return (
              <g
                key={node.individual_id}
                data-person-node
                role="treeitem"
                aria-label={`${node.name}, ${lifeYears(node)}`}
                tabIndex={0}
                className={`tree-node ${selected ? 'selected' : ''} ${inLineage ? 'lineage' : ''}`}
                transform={`translate(${node.x} ${node.y})`}
                onClick={() => onSelect(node.individual_id)}
                onDoubleClick={() => centerOn(node.individual_id, Math.max(transform.scale, 1))}
                onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onSelect(node.individual_id); }}
              >
                <rect width={CARD_W} height={CARD_H} rx="10" />
                <circle cx="19" cy="20" r="8" />
                <text className="tree-node-initial" x="19" y="23" textAnchor="middle">{initials(node.name).slice(0, 1)}</text>
                <text className="tree-node-name" x="34" y="19">{node.name.length > 25 ? `${node.name.slice(0, 24)}…` : node.name}</text>
                <text className="tree-node-years" x="34" y="35">{lifeYears(node)} · {confidenceLabel}</text>
              </g>
            );
          })}
        </g>
      </svg>
      <div className="canvas-legend"><span /> Selected lineage <small>{lineage.ancestors.size} ancestors · {lineage.descendants.size} descendants</small></div>
      <div className="tree-zoom">
        <Button variant="outline" size="icon" onClick={() => zoom(0.82)} aria-label="Zoom out"><Minus /></Button>
        <span>{Math.round(transform.scale * 100)}%</span>
        <Button variant="outline" size="icon" onClick={() => zoom(1.2)} aria-label="Zoom in"><Plus /></Button>
        <Button variant="outline" size="icon" onClick={() => centerOn(selectedId)} aria-label="Center selected person"><Focus /></Button>
      </div>
      <div className="pan-hint"><Hand /> Drag to move · Scroll to zoom · Double-click a person to focus</div>
    </div>
  );
}

function MigrationMap({ data, world, onSelect }: { data: MigrationData; world: unknown; onSelect: (id: string) => void }) {
  const [side, setSide] = useState<'All' | 'Maternal' | 'Paternal'>('All');
  const [routeType, setRouteType] = useState<'intergenerational' | 'lifetime'>('intergenerational');
  const [year, setYear] = useState(data.metadata.year_extent[1]);
  const [playing, setPlaying] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const width = 1000;
  const height = 520;
  const locations = useMemo(() => new Map(data.locations.map((location) => [location.location_id, location])), [data.locations]);
  const projection = useMemo(() => geoNaturalEarth1().fitExtent([[18, 18], [width - 18, height - 18]], { type: 'Sphere' }), []);
  const path = useMemo(() => geoPath(projection), [projection]);
  const countries = useMemo(() => {
    if (!world || typeof world !== 'object' || !('objects' in world)) return [];
    const objects = (world as { objects: Record<string, unknown> }).objects;
    const key = Object.keys(objects)[0];
    if (!key) return [];
    return (feature(world as never, objects[key] as never) as unknown as { features: unknown[] }).features ?? [];
  }, [world]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setYear((current) => current >= data.metadata.year_extent[1] ? data.metadata.year_extent[0] : Math.min(data.metadata.year_extent[1], current + 5));
    }, 120);
    return () => window.clearInterval(timer);
  }, [playing, data.metadata.year_extent]);

  const events = data.events.filter((event) => event.year_min !== null && event.year_min <= year && (side === 'All' || event.side === side));
  const movements = data.movements.filter((movement) => movement.movement_type === routeType && movement.year_min !== null && movement.year_min <= year && (side === 'All' || movement.side === side));
  const pointGroups = useMemo(() => {
    const groups = new Map<string, MapEvent[]>();
    events.forEach((event) => groups.set(event.location_id, [...(groups.get(event.location_id) ?? []), event]));
    return [...groups.entries()].map(([locationId, locationEvents]) => ({ locationId, events: locationEvents, location: locations.get(locationId) })).filter((group) => group.location?.latitude !== null && group.location?.longitude !== null);
  }, [events, locations]);
  const selectedEvents = selectedLocation ? pointGroups.find((point) => point.locationId === selectedLocation)?.events ?? [] : [];

  return (
    <div className="map-stage">
      <div className="map-controls">
        <label><span>Family side</span><NativeSelect value={side} onChange={(event) => setSide(event.target.value as typeof side)}><NativeSelectOption value="All">Both sides</NativeSelectOption><NativeSelectOption value="Maternal">Maternal</NativeSelectOption><NativeSelectOption value="Paternal">Paternal</NativeSelectOption></NativeSelect></label>
        <label><span>Movement</span><NativeSelect value={routeType} onChange={(event) => setRouteType(event.target.value as typeof routeType)}><NativeSelectOption value="intergenerational">Between generations</NativeSelectOption><NativeSelectOption value="lifetime">Within lifetimes</NativeSelectOption></NativeSelect></label>
        <label className="year-control"><span>Through <strong>{year}</strong></span><input type="range" min={data.metadata.year_extent[0]} max={data.metadata.year_extent[1]} value={year} onChange={(event) => setYear(Number(event.target.value))} /></label>
        <Button variant="outline" onClick={() => setPlaying((value) => !value)}>{playing ? <Pause /> : <Play />}{playing ? 'Pause' : 'Play'}</Button>
      </div>
      <div className="map-canvas">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Family birth and death locations over time">
          <path className="map-sphere" d={path({ type: 'Sphere' }) ?? ''} />
          <path className="map-graticule" d={path(geoGraticule10()) ?? ''} />
          {countries.map((country, index) => <path className="map-country" key={index} d={path(country as never) ?? ''} />)}
          {movements.map((movement) => {
            const from = locations.get(movement.from_location_id);
            const to = locations.get(movement.to_location_id);
            if (!from || !to || from.latitude === null || from.longitude === null || to.latitude === null || to.longitude === null) return null;
            return <path key={movement.movement_id} className={`map-route ${movement.side.toLowerCase()} ${movement.movement_type === 'lifetime' ? 'lifetime' : ''}`} d={path({ type: 'LineString', coordinates: [[from.longitude, from.latitude], [to.longitude, to.latitude]] }) ?? ''} />;
          })}
          {pointGroups.map((point) => {
            const location = point.location!;
            const projected = projection([location.longitude!, location.latitude!]);
            if (!projected) return null;
            const dominant = point.events.filter((event) => event.side === 'Maternal').length >= point.events.length / 2 ? 'maternal' : 'paternal';
            return (
              <g key={point.locationId} className={`map-point ${dominant} ${selectedLocation === point.locationId ? 'selected' : ''}`} transform={`translate(${projected[0]} ${projected[1]})`} tabIndex={0} role="button" aria-label={`${location.label}: ${point.events.length} recorded events`} onClick={() => setSelectedLocation(point.locationId)} onKeyDown={(event) => { if (event.key === 'Enter') setSelectedLocation(point.locationId); }}>
                <circle r={Math.min(11, 3.5 + Math.sqrt(point.events.length) * 1.7)} />
                <title>{location.label} · {point.events.length} events</title>
              </g>
            );
          })}
        </svg>
        <div className="map-legend"><span className="dot maternal" /> Maternal <span className="dot paternal" /> Paternal <i /> Inferred endpoint connection</div>
      </div>
      <div className="map-summary">
        <div><strong>{events.length}</strong><span>visible events</span></div>
        <div><strong>{pointGroups.length}</strong><span>locations</span></div>
        <div><strong>{movements.length}</strong><span>connections</span></div>
        <p><CircleAlert /> Connections compare recorded endpoints; they are not documented travel routes.</p>
      </div>
      {selectedEvents.length > 0 && (
        <div className="map-location-detail">
          <Button variant="ghost" size="icon" className="close-map-detail" onClick={() => setSelectedLocation(null)} aria-label="Close location details"><X /></Button>
          <p className="eyebrow">Recorded at this location</p>
          <h3>{locations.get(selectedLocation!)?.label}</h3>
          <div className="map-event-list">
            {selectedEvents.slice().sort((a, b) => (a.year_min ?? 0) - (b.year_min ?? 0)).map((event) => (
              <button key={event.event_id} onClick={() => onSelect(event.person_id)}>
                <span>{event.year_min ?? 'Undated'}</span><strong>{event.person_name}</strong><small>{event.event_type} · {event.branch}</small><ChevronRight />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailsPane({ person, data, relations, onSelect }: { person: Person; data: TreeData; relations: RelationIndex; onSelect: (id: string) => void }) {
  const people = useMemo(() => new Map(data.people.map((item) => [item.individual_id, item])), [data.people]);
  const sources = useMemo(() => new Map(data.sources.map((source) => [source.source_id, source])), [data.sources]);
  const sourceRefs = splitRefs(person.source_refs);
  const records = matchedRecords(person);
  const [confidenceCode, confidenceLabel] = confidenceFromNotes(person.notes);
  const relationships = [
    { label: 'Parents', ids: relations.parents.get(person.individual_id) ?? [] },
    { label: 'Spouses', ids: relations.spouses.get(person.individual_id) ?? [] },
    { label: 'Children', ids: relations.children.get(person.individual_id) ?? [] },
  ];
  const events = [
    person.birth && { label: 'Birth', value: person.birth },
    person.death && { label: 'Death', value: person.death },
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <aside className="detail-panel" aria-label={`${person.name} details`}>
      <div className="detail-heading">
        <div className={`monogram sex-${person.sex.toLowerCase()}`}>{initials(person.name)}</div>
        <div>
          <Badge className={`confidence confidence-${confidenceCode.toLowerCase()}`}>{confidenceCode ? `${confidenceCode} · ${confidenceLabel}` : confidenceLabel}</Badge>
          <h2>{person.name}</h2>
          <p>{lifeYears(person)} · {person.sex === 'M' ? 'Male' : person.sex === 'F' ? 'Female' : 'Sex not recorded'}</p>
        </div>
      </div>

      {events.length > 0 && <section className="detail-block"><p className="eyebrow">Life events</p>{events.map((event) => <div className="life-event" key={event.label}><span>{event.label}</span><strong>{event.value}</strong></div>)}</section>}

      <section className="detail-block">
        <p className="eyebrow">Family</p>
        {relationships.map((relationship) => relationship.ids.length > 0 && (
          <div className="relationship-row" key={relationship.label}>
            <span>{relationship.label}</span>
            <div>{relationship.ids.map((id) => <button key={id} onClick={() => onSelect(id)}>{people.get(id)?.name ?? id}<ChevronRight /></button>)}</div>
          </div>
        ))}
        {relationships.every((relationship) => relationship.ids.length === 0) && <p className="empty-copy">No family relationships are identified in the canonical tree.</p>}
      </section>

      {person.notes && <section className="note-card"><p className="eyebrow">Research notes</p><p>{person.notes}</p></section>}

      <section className="detail-block">
        <p className="eyebrow">Record identifiers</p>
        <dl className="identifier-list"><div><dt>Canonical ID</dt><dd>{person.individual_id}</dd></div>{person.local_ids && <div><dt>Local reference</dt><dd>{person.local_ids}</dd></div>}</dl>
      </section>

      <section className="source-section">
        <div className="section-title"><p className="eyebrow">Evidence · {sourceRefs.length}</p><ShieldCheck size={15} /></div>
        {sourceRefs.length ? sourceRefs.map((ref) => {
          const source = sources.get(ref);
          return source ? <article className="citation-card" key={ref}><span>{ref}</span><div><strong>{source.title}</strong>{source.notes && <p>{source.notes}</p>}<small>{[source.author, source.date, source.origin].filter(Boolean).join(' · ')}</small></div></article> : null;
        }) : <p className="empty-copy">No source reference is attached to this person.</p>}
      </section>

      <section className="record-section">
        <div className="section-title"><p className="eyebrow">Preserved records · {records.length}</p><FileText size={15} /></div>
        {records.length > 0 ? <div className="record-gallery">{records.map((record) => {
          const isPdf = record.endsWith('.pdf');
          return <a href={`/records/${record}`} target="_blank" rel="noreferrer" className="record-card" key={record}>
            <div className="record-preview">{isPdf ? <div className="pdf-preview"><FileText /><span>PDF</span></div> : <img src={`/records/${record}`} alt={`Source record: ${cleanTitle(record)}`} loading="lazy" />}</div>
            <div><strong>{cleanTitle(record)}</strong><span>Open full record <ExternalLink /></span></div>
          </a>;
        })}</div> : <p className="empty-copy">No preserved record image is directly matched to this person. Their citations are still listed above.</p>}
      </section>
    </aside>
  );
}

export default function FamilyExplorer() {
  const [data, setData] = useState<TreeData | null>(null);
  const [migration, setMigration] = useState<MigrationData | null>(null);
  const [world, setWorld] = useState<unknown>(null);
  const [selectedId, setSelectedId] = useState(ROOT_ID);
  const [view, setView] = useState<'tree' | 'map'>('tree');
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch('/data/family-tree.json').then((response) => response.json()),
      fetch('/data/migration-data.json').then((response) => response.json()),
      fetch('/data/world-countries-110m.topojson').then((response) => response.json()),
    ]).then(([treeData, migrationData, worldData]) => {
      setData(treeData as TreeData);
      setMigration(migrationData as MigrationData);
      setWorld(worldData);
    });
  }, []);

  const relations = useMemo(() => data ? buildRelations(data) : null, [data]);
  const selected = data?.people.find((person) => person.individual_id === selectedId) ?? data?.people[0];
  const results = useMemo(() => {
    if (!data || normalize(query).length < 2) return [];
    const needle = normalize(query);
    return data.people.filter((person) => normalize(person.name).includes(needle)).slice(0, 8);
  }, [data, query]);

  if (!data || !migration || !relations || !selected) return <LoadingView />;

  const selectPerson = (id: string) => {
    setSelectedId(id);
    setQuery('');
    setSearchOpen(false);
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark"><Sparkles size={16} /></div>
        <div className="brand-copy"><p className="eyebrow">The Vollmer family archive</p><h1>Lineage</h1></div>
        <div className="view-switch" aria-label="Choose view">
          <Button variant={view === 'tree' ? 'default' : 'ghost'} onClick={() => setView('tree')}><GitBranch /> Tree</Button>
          <Button variant={view === 'map' ? 'default' : 'ghost'} onClick={() => setView('map')}><MapIcon /> Map</Button>
        </div>
        <div className="search-wrap">
          <Search size={16} />
          <Input value={query} onChange={(event) => { setQuery(event.target.value); setSearchOpen(true); }} onFocus={() => setSearchOpen(true)} aria-label="Search family members" placeholder="Find one of 308 people…" />
          {query && <Button variant="ghost" size="icon" className="clear-search" onClick={() => setQuery('')} aria-label="Clear search"><X /></Button>}
          {searchOpen && query.length >= 2 && <div className="search-results">{results.length ? results.map((person) => <button key={person.individual_id} onClick={() => selectPerson(person.individual_id)}><span className="result-monogram">{initials(person.name)}</span><span><strong>{person.name}</strong><small>{lifeYears(person)}</small></span><ChevronRight /></button>) : <p>No matching family members</p>}</div>}
        </div>
      </header>

      <section className="workspace">
        <div className="main-panel">
          <div className="section-toolbar">
            <div>
              <p className="eyebrow">{view === 'tree' ? 'Interactive family tree' : 'Family migration through time'}</p>
              <p className="view-title">{view === 'tree' ? `${data.people.length} people · ${data.families.length} family groups` : `${migration.metadata.counts.people_represented} people across ${migration.metadata.counts.locations} places`}</p>
            </div>
            <div className="privacy-note"><ShieldCheck /> Privacy-aware <span>Living details omitted</span></div>
          </div>
          {view === 'tree' ? <TreeCanvas data={data} relations={relations} selectedId={selectedId} onSelect={selectPerson} /> : <MigrationMap data={migration} world={world} onSelect={selectPerson} />}
        </div>
        <DetailsPane person={selected} data={data} relations={relations} onSelect={selectPerson} />
      </section>
      <footer className="mobile-footer"><Users /> {selected.name}<span>{lifeYears(selected)}</span><Button size="sm" variant="outline" onClick={() => document.querySelector('.detail-panel')?.scrollIntoView({ behavior: 'smooth' })}>View details <Maximize2 /></Button></footer>
    </main>
  );
}
