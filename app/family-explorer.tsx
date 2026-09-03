'use client';
/* eslint-disable next/no-img-element, jsx-a11y/prefer-tag-over-role */

import {
  ArrowDown,
  ArrowUp,
  ChevronRight,
  CircleAlert,
  CornerDownRight,
  ExternalLink,
  FileText,
  GitBranch,
  Images,
  Map as MapIcon,
  Maximize2,
  Pause,
  Play,
  RotateCcw,
  Route,
  Search,
  ShieldCheck,
  Users,
  X,
} from 'lucide-react';
import { feature } from 'topojson-client';
import { geoGraticule10, geoNaturalEarth1, geoPath } from 'd3-geo';
import { useEffect, useMemo, useState } from 'react';

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

type RelationIndex = {
  parents: Map<string, string[]>;
  children: Map<string, string[]>;
  spouses: Map<string, string[]>;
  parentLinks: { parent: string; child: string }[];
  spouseLinks: { left: string; right: string }[];
};

const ROOT_ID = 'I001';
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
        <Route size={17} />
      </div>
      <p className="eyebrow">Vollmer family research</p>
      <h1>Opening your family thread…</h1>
    </main>
  );
}

function ThreadPersonCard({
  person,
  media,
  relation,
  active = false,
  onSelect,
}: {
  person: Person;
  media?: MediaPerson;
  relation: string;
  active?: boolean;
  onSelect: (id: string) => void;
}) {
  const [, confidenceLabel] = confidenceFromNotes(person.notes);

  return (
    <button
      type="button"
      className={`thread-person ${active ? 'active' : ''}`}
      onClick={() => onSelect(person.individual_id)}
      aria-current={active ? 'true' : undefined}
    >
      {media?.portrait_path ? (
        <img
          className="thread-avatar"
          src={assetUrl(media.portrait_path)}
          alt=""
        />
      ) : (
        <span
          className={`thread-avatar initials sex-${person.sex.toLowerCase()}`}
        >
          {initials(person.name)}
        </span>
      )}
      <span className="thread-person-copy">
        <span>{relation}</span>
        <strong>{person.name}</strong>
        <small>
          {lifeYears(person)} · {confidenceLabel}
        </small>
      </span>
      <ChevronRight aria-hidden="true" />
    </button>
  );
}

function FamilyThread({
  data,
  relations,
  mediaByPerson,
  selectedId,
  trail,
  onSelect,
  onTrailSelect,
  onReset,
}: {
  data: TreeData;
  relations: RelationIndex;
  mediaByPerson: Map<string, MediaPerson>;
  selectedId: string;
  trail: string[];
  onSelect: (id: string) => void;
  onTrailSelect: (id: string, index: number) => void;
  onReset: () => void;
}) {
  const people = useMemo(
    () => new Map(data.people.map((person) => [person.individual_id, person])),
    [data.people],
  );
  const selected = people.get(selectedId) ?? data.people[0];
  const parentIds = relations.parents.get(selectedId) ?? [];
  const spouseIds = relations.spouses.get(selectedId) ?? [];
  const childIds = relations.children.get(selectedId) ?? [];
  const parents = parentIds
    .map((id) => people.get(id))
    .filter(Boolean) as Person[];
  const spouses = spouseIds
    .map((id) => people.get(id))
    .filter(Boolean) as Person[];
  const children = childIds
    .map((id) => people.get(id))
    .filter(Boolean) as Person[];
  const lineage = useMemo(
    () => collectLineage(selectedId, relations),
    [selectedId, relations],
  );

  return (
    <div className="thread-stage" role="tree" aria-label="Focused family line">
      <div className="thread-stage-head">
        <div>
          <p className="eyebrow">Current thread</p>
          <nav className="thread-trail" aria-label="People in this family line">
            {trail.map((id, index) => {
              const person = people.get(id);
              if (!person) return null;
              return (
                <span key={`${id}-${index}`}>
                  {index > 0 && <CornerDownRight aria-hidden="true" />}
                  <button
                    type="button"
                    className={id === selectedId ? 'current' : ''}
                    onClick={() => onTrailSelect(id, index)}
                    aria-current={id === selectedId ? 'page' : undefined}
                  >
                    {person.name}
                  </button>
                </span>
              );
            })}
          </nav>
        </div>
        <Button variant="ghost" size="sm" onClick={onReset}>
          <RotateCcw /> Start with Fredric
        </Button>
      </div>

      <div className="thread-flow">
        <section
          className="thread-generation"
          aria-labelledby="parent-generation"
        >
          <div className="thread-step-label" id="parent-generation">
            <ArrowUp />
            <span>
              <strong>Previous generation</strong>
              <small>Choose a parent to follow that line</small>
            </span>
          </div>
          {parents.length ? (
            <div className="thread-choice-row">
              {parents.map((person) => (
                <ThreadPersonCard
                  key={person.individual_id}
                  person={person}
                  media={mediaByPerson.get(person.individual_id)}
                  relation="Parent"
                  onSelect={onSelect}
                />
              ))}
            </div>
          ) : (
            <p className="thread-empty">
              No parents are identified in the canonical tree.
            </p>
          )}
        </section>

        <div className="thread-connector" aria-hidden="true">
          <span />
        </div>

        <section
          className="thread-focus"
          aria-label={`${selected.name}, person in focus`}
        >
          <div className="thread-focus-label">
            <span>In focus</span>
            <small>
              {trail.length} step{trail.length === 1 ? '' : 's'} in this thread
            </small>
          </div>
          <ThreadPersonCard
            person={selected}
            media={mediaByPerson.get(selected.individual_id)}
            relation="Selected person"
            active
            onSelect={onSelect}
          />
          {spouses.length > 0 && (
            <div className="thread-spouses">
              <span>Partner{spouses.length === 1 ? '' : 's'}</span>
              {spouses.map((person) => (
                <button
                  type="button"
                  key={person.individual_id}
                  onClick={() => onSelect(person.individual_id)}
                >
                  {person.name} <ChevronRight />
                </button>
              ))}
            </div>
          )}
        </section>

        <div className="thread-connector" aria-hidden="true">
          <span />
        </div>

        <section
          className="thread-generation"
          aria-labelledby="child-generation"
        >
          <div className="thread-step-label" id="child-generation">
            <ArrowDown />
            <span>
              <strong>Next generation</strong>
              <small>Choose a child to continue the thread</small>
            </span>
          </div>
          {children.length ? (
            <div className="thread-choice-row">
              {children.map((person) => (
                <ThreadPersonCard
                  key={person.individual_id}
                  person={person}
                  media={mediaByPerson.get(person.individual_id)}
                  relation="Child"
                  onSelect={onSelect}
                />
              ))}
            </div>
          ) : (
            <p className="thread-empty">
              No children are identified in the canonical tree.
            </p>
          )}
        </section>
      </div>

      <div className="thread-summary">
        <Route />
        <span>
          <strong>One family line at a time.</strong> Select a parent, partner,
          or child to move the focus.
        </span>
        <small>
          {lineage.ancestors.size} ancestors · {lineage.descendants.size}{' '}
          descendants connected
        </small>
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
  const [trail, setTrail] = useState<string[]>([ROOT_ID]);
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
    setTrail((current) => {
      if (current[current.length - 1] === id) return current;
      const priorIndex = current.lastIndexOf(id);
      return priorIndex >= 0
        ? current.slice(0, priorIndex + 1)
        : [...current, id].slice(-8);
    });
    setQuery('');
    setSearchOpen(false);
  };

  const startLineAt = (id: string) => {
    setSelectedId(id);
    setTrail([id]);
    setQuery('');
    setSearchOpen(false);
  };

  const selectTrailPerson = (id: string, index: number) => {
    setSelectedId(id);
    setTrail((current) => current.slice(0, index + 1));
  };

  const resetLine = () => {
    setSelectedId(ROOT_ID);
    setTrail([ROOT_ID]);
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark">
          <Route size={16} />
        </div>
        <div className="brand-copy">
          <p className="eyebrow">Family research workspace</p>
          <h1>Vollmer Atlas</h1>
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
                    onClick={() => startLineAt(person.individual_id)}
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
                  ? 'Focused family thread'
                  : view === 'map'
                    ? 'Family migration through time'
                    : 'Evidence and photo coverage'}
              </p>
              <p className="view-title">
                {view === 'tree'
                  ? `${selected.name} · one generation at a time`
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
            <FamilyThread
              data={data}
              relations={relations}
              mediaByPerson={mediaByPerson}
              selectedId={selectedId}
              trail={trail}
              onSelect={selectPerson}
              onTrailSelect={selectTrailPerson}
              onReset={resetLine}
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
