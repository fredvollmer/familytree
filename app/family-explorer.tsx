'use client';
/* eslint-disable next/no-img-element, jsx-a11y/prefer-tag-over-role */

import {
  ChevronRight,
  CircleAlert,
  ExternalLink,
  FileText,
  Focus,
  GitBranch,
  Hand,
  Images,
  Map as MapIcon,
  Maximize2,
  Minus,
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
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  NativeSelect,
  NativeSelectOption,
} from '@/components/ui/native-select';

type Person = {
  individual_id: string;
  name: string;
  sex: string;
  birth: string;
  death: string;
  occupations_and_roles: string;
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

type MediaPerson = {
  individual_id: string;
  name: string;
  portrait_status:
    | 'external_photo_page'
    | 'privacy_withheld'
    | 'no_verified_photo_archived';
  portrait_path: string;
  portrait_source_name: string;
  portrait_source_url: string;
  portrait_source_refs: string[];
  portrait_rights: string;
  portrait_note: string;
  evidence_ids: string[];
};

type EvidenceRecord = {
  evidence_id: string;
  media_type: 'image' | 'pdf';
  filename: string;
  file_path: string;
  title: string;
  ledger_refs: string[];
  person_ids: string[];
  canonical_source_refs: string[];
  status:
    | 'supporting'
    | 'supporting_with_uncertainty'
    | 'excluded_identity_control';
  note: string;
  source_platforms: string[];
  page_count: number | null;
  preview_paths: string[];
  sha256: string;
};

type MediaAudit = {
  metadata: {
    audited: string;
    people_audited: number;
    portraits_archived: number;
    external_photo_pages: number;
    privacy_withheld: number;
    no_verified_photo_archived: number;
    evidence_files: number;
    evidence_images: number;
    evidence_pdfs: number;
    pdf_preview_images: number;
    policy: string;
  };
  people: MediaPerson[];
  evidence: EvidenceRecord[];
  external_evidence_checks: {
    person_id: string;
    platform: string;
    url: string;
    status: string;
    note: string;
  }[];
};

type TreeData = {
  metadata: { title: string; updated: string; privacy: string; scope: string };
  people: Person[];
  families: Family[];
  sources: Source[];
  media: MediaAudit;
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
    counts: {
      locations: number;
      events: number;
      movements: number;
      people_represented: number;
    };
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

const ROOT_ID = 'I001';
const CARD_W = 174;
const CARD_H = 52;
const ASSET_BASE = import.meta.env.BASE_URL || '/';
const assetUrl = (path: string) => `${ASSET_BASE}${path.replace(/^\//, '')}`;

const splitRefs = (value = '') =>
  value
    .split(/[;,]/)
    .map((part) => part.trim())
    .filter(Boolean);
const normalize = (value: string) =>
  value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
const confidenceFromNotes = (notes: string) =>
  notes.match(/Confidence\s+([A-C])\s*\(([^)]+)\)/i)?.slice(1) ?? [
    '',
    'Unrated',
  ];
const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
const lifeYears = (person: Person) => {
  const birth = person.birth.match(/\b(1[4-9]\d{2}|20\d{2})\b/)?.[1];
  const death = person.death.match(/\b(1[4-9]\d{2}|20\d{2})\b/)?.[1];
  if (!birth && !death)
    return person.notes.toLowerCase().includes('living')
      ? 'Living'
      : 'Dates unknown';
  return `${birth ?? '?'}–${death ?? ''}`;
};
const portraitLabel = (status: MediaPerson['portrait_status']) => {
  if (status === 'external_photo_page') return 'External photo page located';
  if (status === 'privacy_withheld') return 'Portrait withheld for privacy';
  return 'No verified portrait archived';
};

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
    childIds.forEach((child) =>
      parentIds.forEach((parent) => {
        push(parents, child, parent);
        push(children, parent, child);
        parentLinks.push({ parent, child });
      }),
    );
    if (family.husband_id && family.wife_id) {
      push(spouses, family.husband_id, family.wife_id);
      push(spouses, family.wife_id, family.husband_id);
      spouseLinks.push({ left: family.husband_id, right: family.wife_id });
    }
  });
  return { parents, children, spouses, parentLinks, spouseLinks };
}

function buildLayout(data: TreeData) {
  const generation = new Map<string, number>([[ROOT_ID, 0]]);
  for (let pass = 0; pass < 80; pass += 1) {
    let changed = false;
    data.families.forEach((family) => {
      const adults = [family.husband_id, family.wife_id].filter(Boolean);
      const kids = splitRefs(family.children_ids);
      const knownAdult = adults
        .map((id) => generation.get(id))
        .find((value) => value !== undefined);
      const knownKid = kids
        .map((id) => generation.get(id))
        .find((value) => value !== undefined);
      if (knownAdult !== undefined) {
        adults.forEach((id) => {
          if (!generation.has(id)) {
            generation.set(id, knownAdult);
            changed = true;
          }
        });
        kids.forEach((id) => {
          if (!generation.has(id)) {
            generation.set(id, knownAdult + 1);
            changed = true;
          }
        });
      } else if (knownKid !== undefined) {
        adults.forEach((id) => {
          if (!generation.has(id)) {
            generation.set(id, knownKid - 1);
            changed = true;
          }
        });
      }
    });
    if (!changed) break;
  }

  const fallback = Math.max(...generation.values(), 0) + 1;
  data.people.forEach((person) => {
    if (!generation.has(person.individual_id))
      generation.set(person.individual_id, fallback);
  });
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
    group.forEach((person, index) =>
      nodes.push({
        ...person,
        x: start + index * 194 + 10,
        y: (gen - minGen) * 112 + 44,
        generation: gen,
      }),
    );
  });
  return {
    nodes,
    width,
    height: (levels.length - 1) * 112 + 160,
    generations: levels.length,
  };
}

function collectLineage(selectedId: string, relations: RelationIndex) {
  const all = new Set<string>([selectedId]);
  const ancestors = new Set<string>();
  const descendants = new Set<string>();
  const walk = (
    id: string,
    index: Map<string, string[]>,
    result: Set<string>,
  ) => {
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

function LoadingView() {
  return (
    <main className="loading-view">
      <div className="brand-mark">
        <Sparkles size={17} />
      </div>
      <p className="eyebrow">The Vollmer family archive</p>
      <h1>Opening the family tree…</h1>
    </main>
  );
}

function TreeCanvas({
  data,
  relations,
  mediaByPerson,
  selectedId,
  onSelect,
}: {
  data: TreeData;
  relations: RelationIndex;
  mediaByPerson: Map<string, MediaPerson>;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const stageRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{
    x: number;
    y: number;
    tx: number;
    ty: number;
  } | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 0.72 });
  const [positioned, setPositioned] = useState(false);
  const layout = useMemo(() => buildLayout(data), [data]);
  const nodeMap = useMemo(
    () => new Map(layout.nodes.map((node) => [node.individual_id, node])),
    [layout.nodes],
  );
  const lineage = useMemo(
    () => collectLineage(selectedId, relations),
    [selectedId, relations],
  );

  const centerOn = useCallback(
    (id: string, scale = transform.scale) => {
      const stage = stageRef.current;
      const node = nodeMap.get(id);
      if (!stage || !node) return;
      setTransform({
        x: stage.clientWidth / 2 - (node.x + CARD_W / 2) * scale,
        y: stage.clientHeight / 2 - (node.y + CARD_H / 2) * scale,
        scale,
      });
    },
    [nodeMap, transform.scale],
  );

  useEffect(() => {
    if (positioned || !stageRef.current) return;
    centerOn(ROOT_ID, 0.78);
    setPositioned(true);
  }, [centerOn, positioned]);

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
    const next = Math.max(
      0.22,
      Math.min(2.2, transform.scale * (event.deltaY < 0 ? 1.1 : 0.9)),
    );
    const wx = (px - transform.x) / transform.scale;
    const wy = (py - transform.y) / transform.scale;
    setTransform({ x: px - wx * next, y: py - wy * next, scale: next });
  };

  const pointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if ((event.target as Element).closest('[data-person-node]')) return;
    dragRef.current = {
      x: event.clientX,
      y: event.clientY,
      tx: transform.x,
      ty: transform.y,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const pointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    setTransform((current) => ({
      ...current,
      x: drag.tx + event.clientX - drag.x,
      y: drag.ty + event.clientY - drag.y,
    }));
  };

  return (
    <div
      ref={stageRef}
      className="tree-stage"
      onWheel={wheel}
      onPointerDown={pointerDown}
      onPointerMove={pointerMove}
      onPointerUp={() => {
        dragRef.current = null;
      }}
      onPointerCancel={() => {
        dragRef.current = null;
      }}
    >
      <svg
        width="100%"
        height="100%"
        role="tree"
        aria-label="Interactive family tree"
      >
        <g
          transform={`translate(${transform.x} ${transform.y}) scale(${transform.scale})`}
        >
          {relations.parentLinks.map((link) => {
            const parent = nodeMap.get(link.parent);
            const child = nodeMap.get(link.child);
            if (!parent || !child) return null;
            const active =
              lineage.all.has(link.parent) && lineage.all.has(link.child);
            const x1 = parent.x + CARD_W / 2;
            const y1 = parent.y + CARD_H;
            const x2 = child.x + CARD_W / 2;
            const y2 = child.y;
            const mid = (y1 + y2) / 2;
            return (
              <path
                key={`${link.parent}-${link.child}`}
                className={`tree-link ${active ? 'active' : ''}`}
                d={`M${x1} ${y1} V${mid} H${x2} V${y2}`}
              />
            );
          })}
          {relations.spouseLinks.map((link) => {
            const left = nodeMap.get(link.left);
            const right = nodeMap.get(link.right);
            if (!left || !right || left.generation !== right.generation)
              return null;
            const active =
              lineage.all.has(link.left) && lineage.all.has(link.right);
            return (
              <path
                key={`${link.left}-${link.right}`}
                className={`spouse-link ${active ? 'active' : ''}`}
                d={`M${left.x + CARD_W} ${left.y + CARD_H / 2} H${right.x} `}
              />
            );
          })}
          {layout.nodes.map((node) => {
            const selected = node.individual_id === selectedId;
            const inLineage = lineage.all.has(node.individual_id);
            const [, confidenceLabel] = confidenceFromNotes(node.notes);
            const portrait = mediaByPerson.get(node.individual_id);
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
                onDoubleClick={() =>
                  centerOn(node.individual_id, Math.max(transform.scale, 1))
                }
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ')
                    onSelect(node.individual_id);
                }}
              >
                <rect width={CARD_W} height={CARD_H} rx="10" />
                {portrait?.portrait_path ? (
                  <image
                    className="tree-node-photo"
                    href={assetUrl(portrait.portrait_path)}
                    x="10"
                    y="11"
                    width="18"
                    height="18"
                    preserveAspectRatio="xMidYMid slice"
                  />
                ) : (
                  <>
                    <circle cx="19" cy="20" r="8" />
                    <text
                      className="tree-node-initial"
                      x="19"
                      y="23"
                      textAnchor="middle"
                    >
                      {initials(node.name).slice(0, 1)}
                    </text>
                  </>
                )}
                <text className="tree-node-name" x="34" y="19">
                  {node.name.length > 25
                    ? `${node.name.slice(0, 24)}…`
                    : node.name}
                </text>
                <text className="tree-node-years" x="34" y="35">
                  {lifeYears(node)} · {confidenceLabel}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      <div className="canvas-legend">
        <span /> Selected lineage{' '}
        <small>
          {lineage.ancestors.size} ancestors · {lineage.descendants.size}{' '}
          descendants
        </small>
      </div>
      <div className="tree-zoom">
        <Button
          variant="outline"
          size="icon"
          onClick={() => zoom(0.82)}
          aria-label="Zoom out"
        >
          <Minus />
        </Button>
        <span>{Math.round(transform.scale * 100)}%</span>
        <Button
          variant="outline"
          size="icon"
          onClick={() => zoom(1.2)}
          aria-label="Zoom in"
        >
          <Plus />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => centerOn(selectedId)}
          aria-label="Center selected person"
        >
          <Focus />
        </Button>
      </div>
      <div className="pan-hint">
        <Hand /> Drag to move · Scroll to zoom · Double-click a person to focus
      </div>
    </div>
  );
}

function MigrationMap({
  data,
  world,
  onSelect,
}: {
  data: MigrationData;
  world: unknown;
  onSelect: (id: string) => void;
}) {
  const [side, setSide] = useState<'All' | 'Maternal' | 'Paternal'>('All');
  const [routeType, setRouteType] = useState<'intergenerational' | 'lifetime'>(
    'intergenerational',
  );
  const [year, setYear] = useState(data.metadata.year_extent[1]);
  const [playing, setPlaying] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const width = 1000;
  const height = 520;
  const locations = useMemo(
    () =>
      new Map(
        data.locations.map((location) => [location.location_id, location]),
      ),
    [data.locations],
  );
  const projection = useMemo(
    () =>
      geoNaturalEarth1().fitExtent(
        [
          [18, 18],
          [width - 18, height - 18],
        ],
        { type: 'Sphere' },
      ),
    [],
  );
  const path = useMemo(() => geoPath(projection), [projection]);
  const countries = useMemo(() => {
    if (!world || typeof world !== 'object' || !('objects' in world)) return [];
    const objects = (world as { objects: Record<string, unknown> }).objects;
    const key = Object.keys(objects)[0];
    if (!key) return [];
    return (
      (
        feature(world as never, objects[key] as never) as unknown as {
          features: unknown[];
        }
      ).features ?? []
    );
  }, [world]);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setYear((current) =>
        current >= data.metadata.year_extent[1]
          ? data.metadata.year_extent[0]
          : Math.min(data.metadata.year_extent[1], current + 5),
      );
    }, 120);
    return () => window.clearInterval(timer);
  }, [playing, data.metadata.year_extent]);

  const events = data.events.filter(
    (event) =>
      event.year_min !== null &&
      event.year_min <= year &&
      (side === 'All' || event.side === side),
  );
  const movements = data.movements.filter(
    (movement) =>
      movement.movement_type === routeType &&
      movement.year_min !== null &&
      movement.year_min <= year &&
      (side === 'All' || movement.side === side),
  );
  const pointGroups = useMemo(() => {
    const groups = new Map<string, MapEvent[]>();
    events.forEach((event) =>
      groups.set(event.location_id, [
        ...(groups.get(event.location_id) ?? []),
        event,
      ]),
    );
    return [...groups.entries()]
      .map(([locationId, locationEvents]) => ({
        locationId,
        events: locationEvents,
        location: locations.get(locationId),
      }))
      .filter(
        (group) =>
          group.location?.latitude !== null &&
          group.location?.longitude !== null,
      );
  }, [events, locations]);
  const selectedEvents = selectedLocation
    ? (pointGroups.find((point) => point.locationId === selectedLocation)
        ?.events ?? [])
    : [];

  return (
    <div className="map-stage">
      <div className="map-controls">
        <div className="map-select-control">
          <span>Family side</span>
          <NativeSelect
            aria-label="Family side"
            value={side}
            onChange={(event) => setSide(event.target.value as typeof side)}
          >
            <NativeSelectOption value="All">Both sides</NativeSelectOption>
            <NativeSelectOption value="Maternal">Maternal</NativeSelectOption>
            <NativeSelectOption value="Paternal">Paternal</NativeSelectOption>
          </NativeSelect>
        </div>
        <div className="map-select-control">
          <span>Movement</span>
          <NativeSelect
            aria-label="Movement type"
            value={routeType}
            onChange={(event) =>
              setRouteType(event.target.value as typeof routeType)
            }
          >
            <NativeSelectOption value="intergenerational">
              Between generations
            </NativeSelectOption>
            <NativeSelectOption value="lifetime">
              Within lifetimes
            </NativeSelectOption>
          </NativeSelect>
        </div>
        <label className="year-control">
          <span>
            Through <strong>{year}</strong>
          </span>
          <input
            type="range"
            min={data.metadata.year_extent[0]}
            max={data.metadata.year_extent[1]}
            value={year}
            onChange={(event) => setYear(Number(event.target.value))}
          />
        </label>
        <Button variant="outline" onClick={() => setPlaying((value) => !value)}>
          {playing ? <Pause /> : <Play />}
          {playing ? 'Pause' : 'Play'}
        </Button>
      </div>
      <div className="map-canvas">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="Family birth and death locations over time"
        >
          <path className="map-sphere" d={path({ type: 'Sphere' }) ?? ''} />
          <path className="map-graticule" d={path(geoGraticule10()) ?? ''} />
          {countries.map((country, index) => (
            <path
              className="map-country"
              key={index}
              d={path(country as never) ?? ''}
            />
          ))}
          {movements.map((movement) => {
            const from = locations.get(movement.from_location_id);
            const to = locations.get(movement.to_location_id);
            if (
              !from ||
              !to ||
              from.latitude === null ||
              from.longitude === null ||
              to.latitude === null ||
              to.longitude === null
            )
              return null;
            return (
              <path
                key={movement.movement_id}
                className={`map-route ${movement.side.toLowerCase()} ${movement.movement_type === 'lifetime' ? 'lifetime' : ''}`}
                d={
                  path({
                    type: 'LineString',
                    coordinates: [
                      [from.longitude, from.latitude],
                      [to.longitude, to.latitude],
                    ],
                  }) ?? ''
                }
              />
            );
          })}
          {pointGroups.map((point) => {
            const location = point.location!;
            const projected = projection([
              location.longitude!,
              location.latitude!,
            ]);
            if (!projected) return null;
            const dominant =
              point.events.filter((event) => event.side === 'Maternal')
                .length >=
              point.events.length / 2
                ? 'maternal'
                : 'paternal';
            return (
              <g
                key={point.locationId}
                className={`map-point ${dominant} ${selectedLocation === point.locationId ? 'selected' : ''}`}
                transform={`translate(${projected[0]} ${projected[1]})`}
                tabIndex={0}
                role="button"
                aria-label={`${location.label}: ${point.events.length} recorded events`}
                onClick={() => setSelectedLocation(point.locationId)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter')
                    setSelectedLocation(point.locationId);
                }}
              >
                <circle
                  r={Math.min(11, 3.5 + Math.sqrt(point.events.length) * 1.7)}
                />
                <title>
                  {location.label} · {point.events.length} events
                </title>
              </g>
            );
          })}
        </svg>
        <div className="map-legend">
          <span className="dot maternal" /> Maternal{' '}
          <span className="dot paternal" /> Paternal <i /> Inferred endpoint
          connection
        </div>
      </div>
      <div className="map-summary">
        <div>
          <strong>{events.length}</strong>
          <span>visible events</span>
        </div>
        <div>
          <strong>{pointGroups.length}</strong>
          <span>locations</span>
        </div>
        <div>
          <strong>{movements.length}</strong>
          <span>connections</span>
        </div>
        <p>
          <CircleAlert /> Connections compare recorded endpoints; they are not
          documented travel routes.
        </p>
      </div>
      {selectedEvents.length > 0 && (
        <div className="map-location-detail">
          <Button
            variant="ghost"
            size="icon"
            className="close-map-detail"
            onClick={() => setSelectedLocation(null)}
            aria-label="Close location details"
          >
            <X />
          </Button>
          <p className="eyebrow">Recorded at this location</p>
          <h3>{locations.get(selectedLocation!)?.label}</h3>
          <div className="map-event-list">
            {selectedEvents
              .slice()
              .sort((a, b) => (a.year_min ?? 0) - (b.year_min ?? 0))
              .map((event) => (
                <button
                  key={event.event_id}
                  onClick={() => onSelect(event.person_id)}
                >
                  <span>{event.year_min ?? 'Undated'}</span>
                  <strong>{event.person_name}</strong>
                  <small>
                    {event.event_type} · {event.branch}
                  </small>
                  <ChevronRight />
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EvidencePreview({ record }: { record: EvidenceRecord }) {
  const preview = record.preview_paths[0];
  return preview ? (
    <img
      src={assetUrl(preview)}
      alt={`Evidence preview: ${record.title}`}
      loading="lazy"
    />
  ) : (
    <div className="pdf-preview">
      <FileText />
      <span>{record.media_type.toUpperCase()}</span>
    </div>
  );
}

function DetailsPane({
  person,
  data,
  relations,
  onSelect,
}: {
  person: Person;
  data: TreeData;
  relations: RelationIndex;
  onSelect: (id: string) => void;
}) {
  const people = useMemo(
    () => new Map(data.people.map((item) => [item.individual_id, item])),
    [data.people],
  );
  const sources = useMemo(
    () => new Map(data.sources.map((source) => [source.source_id, source])),
    [data.sources],
  );
  const evidence = useMemo(
    () => new Map(data.media.evidence.map((item) => [item.evidence_id, item])),
    [data.media.evidence],
  );
  const sourceRefs = splitRefs(person.source_refs);
  const personMedia = data.media.people.find(
    (item) => item.individual_id === person.individual_id,
  );
  const records = (personMedia?.evidence_ids ?? [])
    .map((id) => evidence.get(id))
    .filter(Boolean) as EvidenceRecord[];
  const [confidenceCode, confidenceLabel] = confidenceFromNotes(person.notes);
  const relationships = [
    {
      label: 'Parents',
      ids: relations.parents.get(person.individual_id) ?? [],
    },
    {
      label: 'Spouses',
      ids: relations.spouses.get(person.individual_id) ?? [],
    },
    {
      label: 'Children',
      ids: relations.children.get(person.individual_id) ?? [],
    },
  ];
  const events = [
    person.birth && { label: 'Birth', value: person.birth },
    person.death && { label: 'Death', value: person.death },
  ].filter(Boolean) as { label: string; value: string }[];
  const occupations = person.occupations_and_roles
    .split(' | ')
    .map((value) => value.trim())
    .filter(Boolean);

  return (
    <aside className="detail-panel" aria-label={`${person.name} details`}>
      <div className="detail-heading">
        {personMedia?.portrait_path ? (
          <img
            className="portrait-image"
            src={assetUrl(personMedia.portrait_path)}
            alt={`Portrait of ${person.name}`}
          />
        ) : (
          <div className={`monogram sex-${person.sex.toLowerCase()}`}>
            {initials(person.name)}
          </div>
        )}
        <div>
          <Badge
            className={`confidence confidence-${confidenceCode.toLowerCase()}`}
          >
            {confidenceCode
              ? `${confidenceCode} · ${confidenceLabel}`
              : confidenceLabel}
          </Badge>
          <h2>{person.name}</h2>
          <p>
            {lifeYears(person)} ·{' '}
            {person.sex === 'M'
              ? 'Male'
              : person.sex === 'F'
                ? 'Female'
                : 'Sex not recorded'}
          </p>
          {personMedia && (
            <div
              className={`portrait-status portrait-${personMedia.portrait_status}`}
            >
              <Images />{' '}
              <span>{portraitLabel(personMedia.portrait_status)}</span>
            </div>
          )}
          {personMedia?.portrait_source_url && (
            <a
              className="portrait-link"
              href={personMedia.portrait_source_url}
              target="_blank"
              rel="noreferrer"
            >
              Open {personMedia.portrait_source_name}
              <ExternalLink />
            </a>
          )}
        </div>
      </div>

      {events.length > 0 && (
        <section className="detail-block">
          <p className="eyebrow">Life events</p>
          {events.map((event) => (
            <div className="life-event" key={event.label}>
              <span>{event.label}</span>
              <strong>{event.value}</strong>
            </div>
          ))}
        </section>
      )}

      <section className="detail-block">
        <p className="eyebrow">Occupations &amp; service</p>
        {occupations.length > 0 ? (
          occupations.map((occupation) => (
            <div className="life-event" key={occupation}>
              <span>Role</span>
              <strong>{occupation}</strong>
            </div>
          ))
        ) : (
          <p className="empty-copy">
            No supported occupation or service role is recorded for this person.
          </p>
        )}
      </section>

      <section className="detail-block">
        <p className="eyebrow">Family</p>
        {relationships.map(
          (relationship) =>
            relationship.ids.length > 0 && (
              <div className="relationship-row" key={relationship.label}>
                <span>{relationship.label}</span>
                <div>
                  {relationship.ids.map((id) => (
                    <button key={id} onClick={() => onSelect(id)}>
                      {people.get(id)?.name ?? id}
                      <ChevronRight />
                    </button>
                  ))}
                </div>
              </div>
            ),
        )}
        {relationships.every(
          (relationship) => relationship.ids.length === 0,
        ) && (
          <p className="empty-copy">
            No family relationships are identified in the canonical tree.
          </p>
        )}
      </section>

      {person.notes && (
        <section className="note-card">
          <p className="eyebrow">Research notes</p>
          <p>{person.notes}</p>
        </section>
      )}

      <section className="detail-block">
        <p className="eyebrow">Record identifiers</p>
        <dl className="identifier-list">
          <div>
            <dt>Canonical ID</dt>
            <dd>{person.individual_id}</dd>
          </div>
          {person.local_ids && (
            <div>
              <dt>Local reference</dt>
              <dd>{person.local_ids}</dd>
            </div>
          )}
        </dl>
      </section>

      <section className="source-section">
        <div className="section-title">
          <p className="eyebrow">Evidence · {sourceRefs.length}</p>
          <ShieldCheck size={15} />
        </div>
        {sourceRefs.length ? (
          sourceRefs.map((ref) => {
            const source = sources.get(ref);
            return source ? (
              <article className="citation-card" key={ref}>
                <span>{ref}</span>
                <div>
                  <strong>{source.title}</strong>
                  {source.notes && <p>{source.notes}</p>}
                  <small>
                    {[source.author, source.date, source.origin]
                      .filter(Boolean)
                      .join(' · ')}
                  </small>
                </div>
              </article>
            ) : null;
          })
        ) : (
          <p className="empty-copy">
            No source reference is attached to this person.
          </p>
        )}
      </section>

      <section className="record-section">
        <div className="section-title">
          <p className="eyebrow">Preserved records · {records.length}</p>
          <FileText size={15} />
        </div>
        {records.length > 0 ? (
          <div className="record-gallery">
            {records.map((record) => {
              return (
                <a
                  href={assetUrl(record.file_path)}
                  target="_blank"
                  rel="noreferrer"
                  className={`record-card ${record.status === 'excluded_identity_control' ? 'record-excluded' : ''}`}
                  key={record.evidence_id}
                >
                  <div className="record-preview">
                    <EvidencePreview record={record} />
                  </div>
                  <div>
                    <small>
                      {record.evidence_id} · {record.ledger_refs.join(', ')}
                    </small>
                    <strong>{record.title}</strong>
                    {record.status === 'excluded_identity_control' && (
                      <em>Identity control · excluded</em>
                    )}
                    <span>
                      Open full {record.media_type === 'pdf' ? 'PDF' : 'image'}{' '}
                      <ExternalLink />
                    </span>
                  </div>
                </a>
              );
            })}
          </div>
        ) : (
          <p className="empty-copy">
            No preserved record image is directly matched to this person. Their
            citations are still listed above.
          </p>
        )}
      </section>
    </aside>
  );
}

function EvidenceArchive({
  data,
  onSelect,
}: {
  data: TreeData;
  onSelect: (id: string) => void;
}) {
  const [filter, setFilter] = useState('');
  const people = useMemo(
    () => new Map(data.people.map((person) => [person.individual_id, person])),
    [data.people],
  );
  const records = useMemo(() => {
    const needle = normalize(filter);
    if (!needle) return data.media.evidence;
    return data.media.evidence.filter((record) =>
      normalize(
        `${record.title} ${record.filename} ${record.ledger_refs.join(' ')} ${record.person_ids.map((id) => people.get(id)?.name ?? id).join(' ')}`,
      ).includes(needle),
    );
  }, [data.media.evidence, filter, people]);

  return (
    <div className="archive-stage">
      <div className="archive-intro">
        <div>
          <p className="eyebrow">Preserved evidence archive</p>
          <h2>Every available record image, explicitly linked</h2>
          <p>
            {data.media.metadata.evidence_images} source images and{' '}
            {data.media.metadata.evidence_pdfs} PDFs are preserved. The PDFs
            include {data.media.metadata.pdf_preview_images} attached page
            previews for quick review.
          </p>
        </div>
        <div className="archive-search">
          <Search />
          <Input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Filter records, people, or source IDs…"
            aria-label="Filter evidence archive"
          />
        </div>
      </div>
      <div className="archive-metrics">
        <div>
          <strong>{data.media.metadata.people_audited}</strong>
          <span>people photo-audited</span>
        </div>
        <div>
          <strong>{data.media.metadata.external_photo_pages}</strong>
          <span>external photo pages</span>
        </div>
        <div>
          <strong>{data.media.metadata.evidence_files}</strong>
          <span>preserved files</span>
        </div>
        <div>
          <strong>{records.length}</strong>
          <span>records shown</span>
        </div>
      </div>
      <div className="archive-grid">
        {records.map((record) => (
          <article
            className={`archive-card ${record.status === 'excluded_identity_control' ? 'record-excluded' : ''}`}
            key={record.evidence_id}
          >
            <a
              className="archive-image"
              href={assetUrl(record.file_path)}
              target="_blank"
              rel="noreferrer"
            >
              <EvidencePreview record={record} />
              <span>
                {record.media_type === 'pdf'
                  ? `${record.page_count} page PDF`
                  : 'Source image'}{' '}
                <ExternalLink />
              </span>
            </a>
            <div className="archive-card-copy">
              <p className="eyebrow">
                {record.evidence_id} · {record.ledger_refs.join(', ')}
              </p>
              <h3>{record.title}</h3>
              {record.status !== 'supporting' && (
                <Badge variant="outline">
                  {record.status === 'excluded_identity_control'
                    ? 'Excluded identity control'
                    : 'Uncertainty retained'}
                </Badge>
              )}
              {record.note && <p>{record.note}</p>}
              <div className="archive-people">
                {record.person_ids.length ? (
                  record.person_ids.map((id) => (
                    <button key={id} onClick={() => onSelect(id)}>
                      {people.get(id)?.name ?? id}
                    </button>
                  ))
                ) : (
                  <span>No canonical person attached</span>
                )}
              </div>
              <small>
                {record.source_platforms.join(' · ')} ·{' '}
                {record.preview_paths.length} preview
                {record.preview_paths.length === 1 ? '' : 's'}
              </small>
            </div>
          </article>
        ))}
      </div>
      <section className="external-checks">
        <p className="eyebrow">External newspaper checks</p>
        <h2>Links retained when the image could not be preserved</h2>
        <div>
          {data.media.external_evidence_checks.map((check) => (
            <article key={`${check.person_id}-${check.platform}`}>
              <strong>
                {people.get(check.person_id)?.name ?? check.person_id}
              </strong>
              <span>
                {check.platform} · {check.status.replaceAll('_', ' ')}
              </span>
              <p>{check.note}</p>
              {check.url && (
                <a href={check.url} target="_blank" rel="noreferrer">
                  Open source index <ExternalLink />
                </a>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default function FamilyExplorer() {
  const [data, setData] = useState<TreeData | null>(null);
  const [migration, setMigration] = useState<MigrationData | null>(null);
  const [world, setWorld] = useState<unknown>(null);
  const [selectedId, setSelectedId] = useState(ROOT_ID);
  const [view, setView] = useState<'tree' | 'map' | 'archive'>('tree');
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    void Promise.all([
      fetch(assetUrl('data/family-tree.json')).then((response) =>
        response.json(),
      ),
      fetch(assetUrl('data/migration-data.json')).then((response) =>
        response.json(),
      ),
      fetch(assetUrl('data/world-countries-110m.topojson')).then((response) =>
        response.json(),
      ),
    ])
      .then(([treeData, migrationData, worldData]) => {
        setData(treeData as TreeData);
        setMigration(migrationData as MigrationData);
        setWorld(worldData);
      })
      .catch((error) =>
        console.error('Unable to load family archive data.', error),
      );
  }, []);

  const relations = useMemo(() => (data ? buildRelations(data) : null), [data]);
  const mediaByPerson = useMemo(
    () =>
      new Map(
        data?.media.people.map((person) => [person.individual_id, person]) ??
          [],
      ),
    [data],
  );
  const selected =
    data?.people.find((person) => person.individual_id === selectedId) ??
    data?.people[0];
  const results = useMemo(() => {
    if (!data || normalize(query).length < 2) return [];
    const needle = normalize(query);
    return data.people
      .filter((person) => normalize(person.name).includes(needle))
      .slice(0, 8);
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
        <div className="brand-mark">
          <Sparkles size={16} />
        </div>
        <div className="brand-copy">
          <p className="eyebrow">The Vollmer family archive</p>
          <h1>Lineage</h1>
        </div>
        <div className="view-switch" aria-label="Choose view">
          <Button
            variant={view === 'tree' ? 'default' : 'ghost'}
            onClick={() => setView('tree')}
          >
            <GitBranch /> Tree
          </Button>
          <Button
            variant={view === 'map' ? 'default' : 'ghost'}
            onClick={() => setView('map')}
          >
            <MapIcon /> Map
          </Button>
          <Button
            variant={view === 'archive' ? 'default' : 'ghost'}
            onClick={() => setView('archive')}
          >
            <Images /> Evidence
          </Button>
        </div>
        <div className="search-wrap">
          <Search size={16} />
          <Input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setSearchOpen(true);
            }}
            onFocus={() => setSearchOpen(true)}
            aria-label="Search family members"
            placeholder={`Find one of ${data.people.length} people…`}
          />
          {query && (
            <Button
              variant="ghost"
              size="icon"
              className="clear-search"
              onClick={() => setQuery('')}
              aria-label="Clear search"
            >
              <X />
            </Button>
          )}
          {searchOpen && query.length >= 2 && (
            <div className="search-results">
              {results.length ? (
                results.map((person) => (
                  <button
                    key={person.individual_id}
                    onClick={() => selectPerson(person.individual_id)}
                  >
                    <span className="result-monogram">
                      {initials(person.name)}
                    </span>
                    <span>
                      <strong>{person.name}</strong>
                      <small>{lifeYears(person)}</small>
                    </span>
                    <ChevronRight />
                  </button>
                ))
              ) : (
                <p>No matching family members</p>
              )}
            </div>
          )}
        </div>
      </header>

      <section className="workspace">
        <div className="main-panel">
          <div className="section-toolbar">
            <div>
              <p className="eyebrow">
                {view === 'tree'
                  ? 'Interactive family tree'
                  : view === 'map'
                    ? 'Family migration through time'
                    : 'Evidence and photo coverage'}
              </p>
              <p className="view-title">
                {view === 'tree'
                  ? `${data.people.length} people · ${data.families.length} family groups`
                  : view === 'map'
                    ? `${migration.metadata.counts.people_represented} people across ${migration.metadata.counts.locations} places`
                    : `${data.media.metadata.evidence_files} preserved files · ${data.media.metadata.people_audited} people audited`}
              </p>
            </div>
            <div className="privacy-note">
              <ShieldCheck /> Privacy-aware <span>Living details omitted</span>
            </div>
          </div>
          {view === 'tree' ? (
            <TreeCanvas
              data={data}
              relations={relations}
              mediaByPerson={mediaByPerson}
              selectedId={selectedId}
              onSelect={selectPerson}
            />
          ) : view === 'map' ? (
            <MigrationMap
              data={migration}
              world={world}
              onSelect={selectPerson}
            />
          ) : (
            <EvidenceArchive data={data} onSelect={selectPerson} />
          )}
        </div>
        <DetailsPane
          person={selected}
          data={data}
          relations={relations}
          onSelect={selectPerson}
        />
      </section>
      <footer className="mobile-footer">
        <Users /> {selected.name}
        <span>{lifeYears(selected)}</span>
        <Button
          size="sm"
          variant="outline"
          onClick={() =>
            document
              .querySelector('.detail-panel')
              ?.scrollIntoView({ behavior: 'smooth' })
          }
        >
          View details <Maximize2 />
        </Button>
      </footer>
    </main>
  );
}
