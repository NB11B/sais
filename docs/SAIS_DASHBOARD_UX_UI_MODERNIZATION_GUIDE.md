# SAIS Dashboard UX/UI Modernization Guide

## Purpose

SAIS has evolved from a prototype dashboard into a ranch/farm C4ISR command platform. The UI must now communicate authority, clarity, trust, and operational speed.

This guide defines best practices and a modernization plan for making the SAIS dashboard feel less generic and more like a state-of-the-art professional command system.

The design goal is:

```text
operator opens dashboard
→ immediately understands ranch status
→ sees where risk is
→ sees what changed
→ understands why
→ records or dispatches action
→ maintains audit trail
```

---

## Core UX Principle

The dashboard should be organized around operator decisions, not database objects.

Bad hierarchy:

```text
cards
observations
graph nodes
```

Better hierarchy:

```text
current operating picture
urgent risks
domain status
map context
evidence
field actions
asset/node health
```

SAIS should expose data through the operator's mental model:

```text
Water
Forage
Livestock
Soil
Weather
Infrastructure
Assets
Nodes
```

---

## Current UI Assessment

The current dashboard already has several good foundations:

```text
dark command-center theme
Operator Feed / GIS Twin / Knowledge Graph / Admin navigation
RanchHealthCard summary panel
PFKR cards
mobile field-action modals
responsive mobile bottom nav
local Leaflet asset usage in Admin
```

However, the current Operator Feed is still structurally generic. It presents:

```text
Intelligence Cards
Latest Observations
Farm Twin Graph
```

This is useful for development but not optimal for field operators.

The Admin page is also doing too much and still uses developer-oriented inputs such as pasted GeoJSON and free-text IDs.

---

## Best Practice 1: Command Hierarchy

A command dashboard should use a top-down hierarchy:

```text
1. Overall status
2. Priority alerts
3. Domain scorecard
4. Spatial picture
5. Evidence and telemetry
6. Actions and acknowledgments
```

### Recommended Operator Feed Layout

```text
┌──────────────────────────────────────────────────────────┐
│ Ranch Command Header                                     │
│ Overall status | Time | Offline/Online | Source health   │
├──────────────────────────────────────────────────────────┤
│ Priority Strip                                           │
│ ALERTS | ACTION | WATCH | STALE SOURCES | PENDING NODES  │
├──────────────────────────────────────────────────────────┤
│ Domain Scorecard                                         │
│ Water | Forage | Livestock | Soil | Weather | Infra      │
├──────────────────────────────┬───────────────────────────┤
│ Active Intelligence Queue    │ Mini GIS / Asset Context  │
│ sorted by urgency            │ selected item location    │
├──────────────────────────────┴───────────────────────────┤
│ Evidence Drawer / Recent Observations / Audit Trail       │
└──────────────────────────────────────────────────────────┘
```

The first screen should answer:

```text
Is the ranch okay?
What needs attention now?
Where is it?
Why does SAIS think that?
What do I do next?
```

---

## Best Practice 2: Domain-First Navigation

The main navigation should reflect operating surfaces.

Recommended navigation:

```text
Command | Map | Assets | Nodes | Knowledge | Admin
```

Equivalent current mapping:

```text
Command     -> Operator Feed
Map         -> GIS Twin
Assets      -> livestock/water/infra/equipment asset management
Nodes       -> node provisioning/source health
Knowledge   -> Knowledge Graph
Admin       -> farm structure/setup
```

Avoid overloading Admin with daily operations. Admin is configuration. Assets and Nodes are operational management.

---

## Best Practice 3: Alert Triage Before Full Card Feed

Operators should not have to scan a long card list.

Cards should be grouped by status:

```text
ALERT
ACTION
WATCH
STALE
INSUFFICIENT DATA
OK
```

Recommended visual treatment:

```text
alert  -> red, top strip, requires acknowledgement
action -> orange, operational action likely needed
watch  -> amber, monitor or inspect
stale  -> gray/blue, source health issue
ok     -> collapsed by default
```

The default view should show only:

```text
alert
action
watch
stale_data
```

OK cards can be summarized in the scorecard.

---

## Best Practice 4: Evidence Drawer

Every card should have a collapsible evidence drawer.

Card compact view:

```text
Title
Status
Location
Farmer meaning
Suggested inspection/action
```

Expanded view:

```text
Evidence table
source trust
timestamp
freshness
measurement value
PFKR mapping
related assets
related observations
```

Evidence should be tabular and scannable.

Example:

| Source | Measurement | Value | Freshness | Trust |
|---|---:|---:|---:|---|
| soil-node-north | soil.moisture.vwc | 0.21 | 2m ago | accepted |
| weather-station-01 | rainfall | 25 mm | 1h ago | accepted |
| DEM layer | runoff_risk | high | static | derived |

---

## Best Practice 5: Map as Operating Picture

The GIS Twin should become a first-class command surface, not a separate visualization.

Recommended map features:

```text
left layer rail
right selected-object panel
bottom timeline/evidence drawer
status-aware icons
domain filters
search by asset/node/animal/paddock
```

Clicking anything on the map should show:

```text
identity
status
last update
related cards
related sensors/assets
recommended action
history
```

Map objects should include:

```text
farm boundary
fields
zones
paddocks
water assets
infrastructure assets
sensor nodes
livestock/herds
pending nodes/tags
manual observations
```

---

## Best Practice 6: Progressive Disclosure

Do not show all complexity at once.

Use layers:

```text
Level 1: Status
Level 2: Meaning
Level 3: Evidence
Level 4: Raw data
Level 5: Graph/debug
```

The operator should not see raw graph structure unless they choose Knowledge Graph.

---

## Best Practice 7: Field-First Mobile UX

Mobile should be optimized for ranch rounds, not dashboard browsing.

Recommended mobile bottom actions:

```text
Check Water
Check Livestock
Check Forage
Check Soil
Log Issue
Scan Tag
```

Avoid too many colored buttons in the bottom nav. Instead use one floating action button:

```text
+ Log Field Check
```

Then show action sheet:

```text
Water Check
Livestock Check
Plant/Forage Check
Soil Test
Infrastructure Status
Photo Note
RFID Tag Scan
```

This reduces clutter and scales better.

---

## Best Practice 8: Setup Wizard Should Be Guided

The Admin Setup workflow should be a true wizard.

Recommended setup sequence:

```text
1. Farm identity
2. Draw farm boundary
3. Add fields
4. Add paddocks/zones
5. Register assets
6. Provision nodes
7. Confirm source health
8. Review setup completeness
```

Each step should show completion state:

```text
complete
incomplete
needs review
optional
```

The system should generate a `FarmSetupCompletenessCard` when required pieces are missing.

---

## Best Practice 9: Boundary Drawing, Not GeoJSON First

Farm and field boundaries should not require pasted GeoJSON.

Primary boundary workflows:

```text
click map corners
enter lat/lng points
import GeoJSON
upload GPX/KML later
```

Minimum implementation:

```text
corner table
lat/lng inputs
minimum 3 points
preview polygon
auto-close polygon
save as GeoJSON
```

GeoJSON textarea should move to:

```text
Advanced Import
```

---

## Best Practice 10: Capability-Based Node Provisioning

Node provisioning should use capability selection, not only a single node type.

Good model:

```text
Node role: multi-function field node
Capabilities:
  soil moisture
  soil temperature
  humidity
  battery voltage
  RSSI
```

Each capability maps to:

```text
measurement_id
unit
layer
PFKR domains
expected interval
location/asset/zone context
```

The provisioning UI should allow:

```text
single-function node
multi-function node
asset-attached node
mobile/manual device
RFID reader node
camera node
future drone node
```

---

## Best Practice 11: Consistent Status Vocabulary

SAIS should use one status vocabulary across cards, assets, nodes, and sources.

Recommended normalized statuses:

```text
ok
watch
action
alert
stale_data
insufficient_data
insufficient_context
invalid_data
pending
accepted
assigned
active
rejected
retired
```

Do not mix:

```text
open
broken
secure
fault
```

unless they are asset-specific states mapped into the normalized status vocabulary.

Example:

```text
gate.open -> alert
gate.closed -> ok
fence.broken -> action/alert
node.pending -> pending
node.last_seen expired -> stale_data
```

---

## Best Practice 12: Design Tokens and Component System

Create a small design system instead of one-off CSS.

Recommended tokens:

```text
colors
spacing
radius
shadow
font sizes
status colors
z-index layers
breakpoints
```

Recommended components:

```text
CommandHeader
PriorityStrip
DomainScorecard
StatusBadge
IntelligenceCard
EvidenceDrawer
AssetCard
NodeProvisionCard
LayerToggle
MapPopup
ActionSheet
Modal
FormField
EmptyState
StaleSourceBanner
```

This lets the UI feel consistent as pages grow.

---

## Best Practice 13: Typography and Density

Professional dashboards should be dense but not cramped.

Recommendations:

```text
Use one display font only in logo/header.
Use one UI font for everything else.
Use 12/14/16/20/24 px type scale.
Use uppercase sparingly for labels.
Use tabular numbers for metrics.
Avoid long paragraphs inside cards.
```

Card body should use short operational language:

```text
Bad:
This card indicates that the livestock may possibly have elevated risk...

Good:
Tank level is critical while herd is active in Paddock 1.
Inspect water source or move herd.
```

---

## Best Practice 14: Trust and Source Health Visibility

The UI should always indicate source trust.

Evidence should show:

```text
accepted node
pending node
stale node
manual observation
derived layer
open data
unknown source
```

Recommended badges:

```text
trusted
pending
stale
manual
derived
open-data
low-confidence
```

Never hide uncertainty.

---

## Best Practice 15: Offline State Must Be Visible

SAIS is offline-first, so the UI should show:

```text
local mode
internet unavailable
local tiles active
last sync time
open data unavailable
sensor network healthy/unhealthy
```

The operator should know when missing external data is normal and when sensor data is stale.

---

## Recommended New Information Architecture

### Command Page

```text
Ranch status
priority alerts
domain scorecard
active intelligence queue
recent field actions
source health summary
```

### Map Page

```text
GIS operating picture
layers
assets
nodes
livestock/herds
card overlays
selected object detail panel
```

### Assets Page

```text
livestock
water
infrastructure
equipment
media/photos
```

### Nodes Page

```text
pending nodes
active nodes
stale/error nodes
role templates
capabilities
```

### Admin Setup Page

```text
farm identity
farm boundary
fields
zones
paddocks
source/layer defaults
setup completeness
```

### Knowledge Page

```text
graph explorer
evidence chains
PFKR mappings
raw objects
for engineers/audit
```

---

## Visual Direction

SAIS should feel like:

```text
mission control
field operations
geospatial intelligence
industrial reliability
ranch practicality
```

Avoid:

```text
generic SaaS dashboard
crypto dashboard aesthetic
AI toy interface
busy military cosplay
consumer farm app softness
```

Recommended style:

```text
dark graphite base
muted earth/field tones
high-contrast status colors
thin borders
clear typography
map-first spatial language
minimal animation
status-driven glow only for active alerts
```

---

## Proposed WP24: Dashboard UX/UI Modernization

### WP24A: Information Architecture

```text
rename Operator Feed to Command
add Assets route
add Nodes route
separate Admin Setup from ongoing operations
```

### WP24B: Command Page Redesign

```text
RanchHealthCard always visible
priority strip
PFKR/domain scorecard
active intelligence queue sorted by severity
collapse OK cards
source health summary
```

### WP24C: Card Component Redesign

```text
compact card
status badge
location chip
PFKR chip
evidence drawer
action buttons
acknowledge/resolved states
```

### WP24D: Mobile Action Sheet

```text
replace many bottom action buttons with one field-action button
action sheet for water/livestock/plant/soil/infra/photo/tag scan
```

### WP24E: Admin UX Cleanup

```text
boundary point builder
entity dropdowns
setup completeness
GeoJSON advanced import only
```

### WP24F: Node and Asset UX

```text
pending node queue
capability multi-select
asset classes
livestock photo/ID workflow foundation
```

### WP24G: Design System

```text
create dashboard components and tokens
status classes
badges
buttons
forms
empty states
modals
drawers
```

---

## Implementation Priority

Do this in order:

```text
1. Rename/reframe navigation around Command, Map, Assets, Nodes, Admin, Knowledge.
2. Redesign Command page hierarchy.
3. Collapse OK cards and prioritize alert/action/watch/stale.
4. Add evidence drawer pattern.
5. Replace mobile bottom action clutter with action sheet.
6. Move livestock/water/infra/node management into Assets/Nodes pages.
7. Add Admin boundary builder and dropdowns.
8. Extract reusable components/styles.
```

---

## Success Criteria

The UI modernization is successful when:

```text
operator sees top risk in under 5 seconds
operator can identify affected location in under 10 seconds
operator can inspect evidence in one click
operator can log a field check from mobile in two taps
operator can provision a node without typing IDs
operator can draw farm boundary without knowing GeoJSON
operator can distinguish trusted/stale/pending evidence visually
OK state is summarized, not cluttering the feed
```

---

## Bottom Line

SAIS should look and behave like a professional command platform, not a generic dashboard.

The right UI model is:

```text
Command first
Map second
Assets and Nodes operationally separated
Admin for setup only
Knowledge Graph for explainability and audit
```

Every design decision should support the operator's real question:

```text
What is happening, where, why, and what should I do next?
```
