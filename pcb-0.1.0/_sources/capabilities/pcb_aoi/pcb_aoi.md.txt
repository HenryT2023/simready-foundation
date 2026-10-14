# PCB AOI

Capabilities in this category define the **USD contract** for a printed circuit board and its
components: what a board, a component package, or a populated assembly must carry as a USD asset
so that every component, pin, pad and hole can be discovered by attribute and role. The
motivating consumer is an AOI (automated optical inspection) synthetic-data pipeline that renders
the board and simulates solder and component defects; the rules apply to the asset regardless of
what produced it.

The contract is organized by requirement codes **CI / CG / BG / UO** (four capabilities) and
composed into six features cut along the export workflow — `FET_211_STANDARD` component identity,
`FET_212_STANDARD` component geometry, `FET_213_STANDARD` board geometry, `FET_214_STANDARD` USD
core, `FET_215_STANDARD` AOI appearance, `FET_216_STANDARD` delivery package — which the
[`PCB-Assembly`](/profiles/pcb_assembly) profile composes for a populated board and, for the
board-level subset, the [`PCB-Board`](/profiles/pcb_board) profile. Attributes use
the sub-namespaced `pcba:` convention (`pcba:component:*`, `pcba:mesh:*`, `pcba:pin:*`,
`pcba:board:*`).

```{toctree}
:maxdepth: 1

Component Identity <component_identity/capability-component_identity>
Component Geometry <component_geometry/capability-component_geometry>
Board Geometry <board_geometry/capability-board_geometry>
USD Organization <usd_organization/capability-usd_organization>
```
