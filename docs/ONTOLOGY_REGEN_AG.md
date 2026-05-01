# Ontological Map of Regenerative Agriculture

This document defines the foundational ontology of regenerative agriculture for the Sovereign Ag-Infrastructure Stack (SAIS). It serves as the conceptual schema for the SAIS Intelligence Platform's knowledge graph, mapping the biological, chemical, and physical realities of the farm ecosystem directly to the sensor arrays that measure them.

## 1. Foundational Principles

Regenerative agriculture is not a prescriptive set of practices, but a systems-based approach to restoring ecosystem function. The ontology is built upon the five core principles of soil health [1]:

1.  **Minimize Soil Disturbance:** Reducing mechanical (tillage) and chemical (synthetic fertilizers/pesticides) disturbances to protect the soil food web and aggregate structure.
2.  **Maximize Soil Cover:** Keeping the soil armored with living plants or crop residue to regulate temperature, retain moisture, and prevent erosion.
3.  **Maximize Biodiversity:** Cultivating a diverse range of plant species to foster a diverse underground microbial community.
4.  **Maintain Continuous Living Roots:** Ensuring plants are actively growing for as much of the year as possible to provide a continuous supply of carbon exudates to soil microbes.
5.  **Integrate Livestock:** Using adaptive grazing to recycle nutrients, stimulate plant growth, and inoculate the soil with biological life.

## 2. The Soil Food Web: The Biological Engine

At the core of the regenerative ontology is the soil food web—the community of organisms that drive nutrient cycling and soil structure formation [2].

### Trophic Levels

*   **First Trophic Level (Photosynthesizers):** Plants capture solar energy and atmospheric carbon, converting them into sugars. A significant portion of these sugars is released into the rhizosphere as root exudates to feed microbes [3].
*   **Second Trophic Level (Decomposers and Mutualists):** Bacteria and fungi consume root exudates and decompose organic matter. Fungi (especially mycorrhizal networks) extend the root system's reach, while bacteria specialize in rapid nutrient processing.
*   **Third Trophic Level (Shredders and Predators):** Protozoa, nematodes, and microarthropods graze on bacteria and fungi. This predation releases nutrients (like nitrogen) in plant-available forms.
*   **Higher Trophic Levels:** Earthworms, larger insects, and vertebrates further process organic matter and engineer soil structure.

## 3. Ontological Entities and Relationships

The SAIS knowledge graph categorizes the farm ecosystem into distinct entities, tracking the dynamic relationships between them.

### 3.1 Soil Biology (The Drivers)

Soil biology is the active engine of the system.

*   **Entities:** Bacteria, Fungi, Protozoa, Nematodes.
*   **Key Metrics:** Respiration Rate (CO₂ flux), Fungal-to-Bacterial Ratio, Active Carbon.
*   **Relationships:**
    *   *Drives* Soil Chemistry (mineralizes nutrients).
    *   *Builds* Soil Physics (creates aggregates via glomalin and hyphae).

### 3.2 Soil Chemistry (The Fuel)

Soil chemistry represents the nutrient inventory and chemical environment.

*   **Entities:** Macronutrients (NPK), Micronutrients, Soil Organic Carbon (SOC), pH.
*   **Key Metrics:** Total Nitrogen, Potentially Mineralizable Nitrogen, Cation Exchange Capacity (CEC).
*   **Relationships:**
    *   *Nourishes* Plant Health.
    *   *Regulated by* Soil Biology.

### 3.3 Soil Physics (The Habitat)

Soil physics defines the structural and environmental conditions of the habitat.

*   **Entities:** Soil Aggregates, Pore Space, Moisture, Temperature.
*   **Key Metrics:** Bulk Density, Infiltration Rate, Volumetric Water Content.
*   **Relationships:**
    *   *Determines* habitat viability for Soil Biology.
    *   *Modified by* Management Practices.

### 3.4 Plant Health (The Solar Collectors)

Plants are the primary producers, converting sunlight into the carbon currency that runs the system.

*   **Entities:** Cash Crops, Cover Crops, Forage.
*   **Key Metrics:** Brix Level (sap sugar content), Leaf Area Index, Root Depth.
*   **Relationships:**
    *   *Feeds* Soil Biology (via root exudates).
    *   *Protects* Soil Physics (canopy cover).

### 3.5 Management Practices (The Interventions)

Human actions that steer the ecosystem.

*   **Entities:** No-Till, Cover Cropping, Adaptive Grazing, Compost Application.
*   **Relationships:**
    *   *Stimulates* or *Suppresses* Soil Biology.
    *   *Alters* Soil Physics and Chemistry.

## 4. Sensor Mappings

To make this ontology actionable, SAIS maps these conceptual entities to physical sensor packages.

| Ontological Entity | Key Metric | SAIS Sensor Package | Measurement Frequency |
| :--- | :--- | :--- | :--- |
| **Soil Biology** | Respiration Rate (CO₂ flux) | Package 9 (SCD41 Flux Chamber) | 5-minute cycles |
| **Soil Physics** | Temperature | Package 9 (DS18B20) | Continuous |
| **Soil Physics** | Volumetric Water Content | Package 1 (Capacitive Moisture) | Continuous |
| **Soil Chemistry** | NPK Levels | Package 1 (NPK Probe) | Daily |
| **Plant Health** | Brix Level | Manual Input (Refractometer) | Weekly |

## 5. The Closed-Loop Intelligence Cycle

The SAIS Intelligence Platform uses this ontology to move from observation to action:

1.  **Observe:** Package 9 detects a sustained drop in soil respiration (Soil Biology).
2.  **Contextualize:** The system checks Soil Physics (temperature/moisture are optimal) and Management Practices (a fungicide was recently applied).
3.  **Diagnose:** The knowledge graph infers that the fungicide suppressed the fungal population, halting nutrient mineralization.
4.  **Act:** The system recommends a compost tea application (Management Practice) to re-inoculate the Soil Biology.

## References

[1] Noble Research Institute. "The Fundamental Principles of Regenerative Agriculture and Soil Health." https://www.noble.org/regenerative-agriculture/soil/the-fundamental-principles-of-regenerative-agriculture-and-soil-health/
[2] UC Davis Nematology. "Soil Foodwebs." http://nemaplex.ucdavis.edu/ecology/foodwebs.htm
[3] Korenblum, E., et al. "Rhizosphere microbiome mediates systemic root metabolite exudation by root-to-root signaling." *Proceedings of the National Academy of Sciences* 117.7 (2020): 3874-3883.

## 6. The Water Cycle Layer

The small water cycle is the movement of water that originates on land and moves over land, responsible for up to two-thirds of local rainfall [4]. Regenerative agriculture restores this cycle by maximizing infiltration and transpiration.

### 6.1 Hydrology Entities

*   **Entities:** Infiltration, Evapotranspiration, Groundwater Recharge, Runoff.
*   **Key Metrics:** Infiltration Rate (in/hr), Soil Moisture Retention Capacity, Transpiration Volume.
*   **Relationships:**
    *   *Regulated by* Soil Physics (aggregate stability dictates infiltration).
    *   *Driven by* Plant Health (canopy cover drives transpiration).
    *   *Disrupted by* Management Practices (tillage causes runoff).

## 7. The Atmosphere Layer

The atmospheric layer tracks the exchange of greenhouse gases between the farm ecosystem and the air.

### 7.1 Gas Flux Entities

*   **Entities:** Carbon Dioxide (CO₂), Methane (CH₄), Nitrous Oxide (N₂O).
*   **Key Metrics:** Net Carbon Flux, Enteric Methane Emissions, N₂O Volatilization.
*   **Relationships:**
    *   *Sequestered by* Plant Health (photosynthesis).
    *   *Emitted by* Soil Biology (respiration) and Livestock (enteric fermentation).
    *   *Mitigated by* Management Practices (rotational grazing reduces net CH₄ impact).

## 8. The Livestock Integration Layer

Livestock are not just consumers; they are biological inoculators and nutrient cyclers.

### 8.1 Animal Entities

*   **Entities:** Ruminants (Cattle, Sheep), Monogastrics (Pigs, Poultry), Manure/Urine.
*   **Key Metrics:** Stocking Density, Rest Period, Forage Utilization Rate.
*   **Relationships:**
    *   *Inoculates* Soil Biology (rumen microbes transferred to soil).
    *   *Cycles* Soil Chemistry (manure returns NPK).
    *   *Prunes* Plant Health (grazing stimulates root shedding and regrowth).

## 9. The Farm Ecosystem Layer

This layer encompasses the broader biodiversity that supports the agricultural operation.

### 9.1 Biodiversity Entities

*   **Entities:** Pollinators, Predators (Insects/Birds), Wildlife.
*   **Key Metrics:** Species Richness, Predator-Prey Ratios, Habitat Connectivity.
*   **Relationships:**
    *   *Protects* Plant Health (pest control).
    *   *Supported by* Management Practices (buffer strips, diverse cover crops).

## 10. The Market and Financial Layer

The ultimate output of the regenerative system is not just yield, but verifiable ecosystem services that can be monetized.

### 10.1 Economic Entities

*   **Entities:** Carbon Credits, Ecosystem Service Payments, Input Costs, Yield.
*   **Key Metrics:** Verified Carbon Units (VCUs), Profit per Acre, ROI.
*   **Relationships:**
    *   *Generated by* Soil Chemistry (SOC increases).
    *   *Verified by* Sensor Nodes (SAIS data logging).
    *   *Improves* via Management Practices (reduced synthetic inputs).

## Expanded References

[4] Regenified. "Understanding the Small Water Cycle." https://regenified.com/understanding-the-small-water-cycle/
[5] Teague, R., et al. "The role of ruminants in reducing agriculture's carbon footprint in North America." *Journal of Soil and Water Conservation* 71.2 (2016): 156-164.
[6] Gosnell, H., et al. "A cognitive transition: Shift to holistic management." *Ecology and Society* 24.3 (2019).
