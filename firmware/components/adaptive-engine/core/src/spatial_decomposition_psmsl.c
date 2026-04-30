/**
 * @file spatial_decomposition_psmsl.c
 * @brief PSMSL-based spatial mode decomposition implementation
 * 
 * Replaces FFT-based analysis with covariance geometry and
 * Grassmann manifold tracking for 7 semantic sectors.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "spatial_decomposition_psmsl.h"
#include "psmsl_eigen.h"
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Sector Names
// =============================================================================

static const char* sector_names[SPATIAL_PSMSL_NUM_SECTORS] = {
    "Foundation",   // 20-80 Hz
    "Structure",    // 80-200 Hz
    "Body",         // 200-500 Hz
    "Presence",     // 500-2000 Hz
    "Clarity",      // 2000-5000 Hz
    "Air",          // 5000-10000 Hz
    "Extension"     // 10000-20000 Hz
};

// Sector center frequencies (geometric mean of boundaries)
static const float sector_center_freq[SPATIAL_PSMSL_NUM_SECTORS] = {
    40.0f,      // sqrt(20 * 80)
    126.5f,     // sqrt(80 * 200)
    316.2f,     // sqrt(200 * 500)
    1000.0f,    // sqrt(500 * 2000)
    3162.3f,    // sqrt(2000 * 5000)
    7071.1f,    // sqrt(5000 * 10000)
    14142.1f    // sqrt(10000 * 20000)
};

// =============================================================================
// Private Functions
// =============================================================================

/**
 * @brief Compute sector projection weights from mic geometry
 * 
 * Each sector has different spatial characteristics based on wavelength.
 * Low frequencies (long wavelength) are more omnidirectional.
 * High frequencies (short wavelength) are more directional.
 */
static void compute_sector_weights(spatial_psmsl_analyzer_t *analyzer)
{
    const mic_array_geometry_t *geom = &analyzer->geometry;
    uint8_t n = analyzer->num_mics;
    
    // Clear weights
    memset(analyzer->sector_weights, 0, sizeof(analyzer->sector_weights));
    
    for (uint8_t s = 0; s < SPATIAL_PSMSL_NUM_SECTORS; s++) {
        float freq = sector_center_freq[s];
        float wavelength = 343.0f / freq;  // Speed of sound / frequency
        
        for (uint8_t m = 0; m < n; m++) {
            // Calculate mic position relative to center
            float r = sqrtf(geom->x[m] * geom->x[m] + geom->y[m] * geom->y[m]);
            float theta = atan2f(geom->y[m], geom->x[m]);
            
            // Phase factor based on position and wavelength
            float phase_factor = 2.0f * M_PI * r / wavelength;
            
            // Weight combines spatial and frequency characteristics
            // Low sectors: more uniform weighting (omnidirectional)
            // High sectors: more position-dependent (directional)
            float directivity = 1.0f - expf(-freq / 1000.0f);  // 0 at low freq, ~1 at high
            
            // Base weight (equal for omnidirectional)
            float weight = 1.0f / n;
            
            // Add directional component for higher sectors
            if (r > 0.001f && s >= SPATIAL_SECTOR_PRESENCE) {
                weight += directivity * cosf(theta) * 0.5f / n;
            }
            
            analyzer->sector_weights[s][m] = weight;
        }
    }
}

/**
 * @brief Compute Leibniz-Bocker diagnostics from PSMSL result
 */
static void compute_lb_diagnostics(spatial_psmsl_analyzer_t *analyzer)
{
    spatial_psmsl_result_t *result = &analyzer->result;
    const psmsl_result_t *psmsl = psmsl_get_result(&analyzer->psmsl);
    
    if (!psmsl || !psmsl->valid) {
        result->coherence = 0.0f;
        result->curvature = 0.0f;
        result->residual = 1.0f;
        return;
    }
    
    // Copy diagnostics from PSMSL analyzer
    result->coherence = psmsl->diagnostics.coherence;
    result->curvature = psmsl->diagnostics.curvature;
    result->residual = psmsl->diagnostics.residual;
    result->stability = psmsl->diagnostics.stability;
    result->novelty = psmsl->diagnostics.novelty;
}

/**
 * @brief Compute Grassmann manifold curvature from subspace evolution
 */
static void compute_grassmann_curvature(spatial_psmsl_analyzer_t *analyzer)
{
    spatial_psmsl_result_t *result = &analyzer->result;
    
    if (!analyzer->has_previous_subspace) {
        result->grassmann_distance = 0.0f;
        result->principal_angle_max = 0.0f;
        return;
    }
    
    // Compute geodesic distance on Grassmann manifold
    result->grassmann_distance = grassmann_distance(
        analyzer->subspace_prev,
        analyzer->subspace_curr,
        GRASSMANN_MAX_N,
        PSMSL_NUM_SECTORS
    );
    
    // Compute principal angles
    float angles[GRASSMANN_MAX_K];
    grassmann_principal_angles(
        analyzer->subspace_prev,
        analyzer->subspace_curr,
        angles,
        GRASSMANN_MAX_N,
        PSMSL_NUM_SECTORS
    );
    
    // Find maximum principal angle
    result->principal_angle_max = 0.0f;
    for (uint8_t i = 0; i < PSMSL_NUM_SECTORS; i++) {
        if (angles[i] > result->principal_angle_max) {
            result->principal_angle_max = angles[i];
        }
    }
    
    // Update curvature based on Grassmann distance
    // This provides a geometric measure of structural change
    result->curvature = result->grassmann_distance;
}

/**
 * @brief Extract sector results from PSMSL analysis
 */
static void extract_sector_results(spatial_psmsl_analyzer_t *analyzer)
{
    spatial_psmsl_result_t *result = &analyzer->result;
    const psmsl_result_t *psmsl = psmsl_get_result(&analyzer->psmsl);
    
    if (!psmsl || !psmsl->valid) {
        return;
    }
    
    float total_energy = 0.0f;
    float weighted_freq = 0.0f;
    float weighted_freq_sq = 0.0f;
    
    for (uint8_t s = 0; s < SPATIAL_PSMSL_NUM_SECTORS; s++) {
        spatial_sector_result_t *sector = &result->sectors[s];
        const psmsl_sector_result_t *psmsl_sector = &psmsl->sectors[s];
        
        sector->center_freq = sector_center_freq[s];
        sector->energy_linear = psmsl_sector->energy_linear;
        sector->energy_db = psmsl_sector->energy_db;
        sector->coherence = psmsl_sector->sector_coherence;
        sector->phase = psmsl_sector->phase;
        sector->phi_weight = psmsl_sector->phi_weight;
        sector->eigenvalue_ratio = psmsl_sector->eigenvalue_ratio;
        
        // Accumulate for summary metrics
        total_energy += sector->energy_linear;
        weighted_freq += sector->energy_linear * sector->center_freq;
        weighted_freq_sq += sector->energy_linear * sector->center_freq * sector->center_freq;
    }
    
    // Compute summary metrics
    result->total_energy_db = 10.0f * log10f(total_energy + 1e-10f);
    
    if (total_energy > 1e-10f) {
        result->spectral_centroid = weighted_freq / total_energy;
        float mean_freq = result->spectral_centroid;
        result->spectral_spread = sqrtf(weighted_freq_sq / total_energy - mean_freq * mean_freq);
    } else {
        result->spectral_centroid = 1000.0f;
        result->spectral_spread = 0.0f;
    }
}

/**
 * @brief Estimate DOA from sector coherence patterns
 */
static void estimate_doa_internal(spatial_psmsl_analyzer_t *analyzer)
{
    spatial_psmsl_result_t *result = &analyzer->result;
    spatial_doa_estimate_t *doa = &result->doa;
    
    // Use sector coherence patterns to estimate direction
    // Higher coherence in a sector suggests a dominant direction
    
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    float total_weight = 0.0f;
    
    for (uint8_t s = 0; s < SPATIAL_PSMSL_NUM_SECTORS; s++) {
        float coherence = result->sectors[s].coherence;
        float phase = result->sectors[s].phase;
        float energy = result->sectors[s].energy_linear;
        
        // Weight by coherence and energy
        float weight = coherence * energy;
        
        sum_x += weight * cosf(phase);
        sum_y += weight * sinf(phase);
        total_weight += weight;
    }
    
    if (total_weight > 1e-6f) {
        doa->azimuth = atan2f(sum_y, sum_x) * 180.0f / M_PI;
        doa->confidence = sqrtf(sum_x * sum_x + sum_y * sum_y) / total_weight;
        doa->elevation = 0.0f;  // 2D array
        doa->spread = (1.0f - doa->confidence) * 180.0f;
    } else {
        doa->azimuth = 0.0f;
        doa->confidence = 0.0f;
        doa->elevation = 0.0f;
        doa->spread = 180.0f;
    }
}

/**
 * @brief Update Grassmann subspace from eigenvectors
 */
static void update_subspace(spatial_psmsl_analyzer_t *analyzer)
{
    // Save previous subspace
    if (analyzer->has_previous_subspace) {
        memcpy(analyzer->subspace_prev, analyzer->subspace_curr, 
               sizeof(analyzer->subspace_prev));
    }
    
    // Extract top-k eigenvectors to form current subspace
    grassmann_update_subspace(
        (const float (*)[GRASSMANN_MAX_N])analyzer->psmsl.eigenvectors,
        analyzer->subspace_curr,
        PSMSL_K_DIMENSIONS,
        PSMSL_NUM_SECTORS
    );
    
    analyzer->has_previous_subspace = true;
}

// =============================================================================
// Initialization Functions
// =============================================================================

bool spatial_psmsl_init(spatial_psmsl_analyzer_t *analyzer,
                        float sample_rate,
                        const mic_array_geometry_t *geometry)
{
    if (!analyzer || !geometry) {
        return false;
    }
    
    memset(analyzer, 0, sizeof(spatial_psmsl_analyzer_t));
    
    analyzer->sample_rate = sample_rate;
    analyzer->num_mics = MIC_ARRAY_CHANNELS;
    memcpy(&analyzer->geometry, geometry, sizeof(mic_array_geometry_t));
    
    // Initialize PSMSL analyzer
    if (!psmsl_init(&analyzer->psmsl, sample_rate, MIC_ARRAY_CHANNELS)) {
        return false;
    }
    
    // Compute sector projection weights
    compute_sector_weights(analyzer);
    
    analyzer->initialized = true;
    analyzer->has_previous_subspace = false;
    
    return true;
}

void spatial_psmsl_reset(spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return;
    
    psmsl_reset(&analyzer->psmsl);
    memset(&analyzer->result, 0, sizeof(spatial_psmsl_result_t));
    memset(analyzer->history, 0, sizeof(analyzer->history));
    analyzer->history_index = 0;
    analyzer->has_previous_subspace = false;
}

void spatial_psmsl_set_geometry(spatial_psmsl_analyzer_t *analyzer,
                                const mic_array_geometry_t *geometry)
{
    if (!analyzer || !geometry) return;
    
    memcpy(&analyzer->geometry, geometry, sizeof(mic_array_geometry_t));
    compute_sector_weights(analyzer);
}

bool spatial_psmsl_calibrate(spatial_psmsl_analyzer_t *analyzer,
                             const float *const *ref_data,
                             uint32_t frames)
{
    if (!analyzer || !ref_data) return false;
    
    // Calibrate PSMSL analyzer
    if (!psmsl_calibrate(&analyzer->psmsl, ref_data, frames)) {
        return false;
    }
    
    analyzer->calibrated = true;
    return true;
}

// =============================================================================
// Analysis Functions
// =============================================================================

bool spatial_psmsl_feed(spatial_psmsl_analyzer_t *analyzer,
                        const float *const *mic_data,
                        uint32_t frames)
{
    if (!analyzer || !analyzer->initialized || !mic_data) {
        return false;
    }
    
    return psmsl_feed(&analyzer->psmsl, mic_data, frames);
}

bool spatial_psmsl_process(spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer || !analyzer->initialized) {
        return false;
    }
    
    // Process PSMSL analysis
    if (!psmsl_process(&analyzer->psmsl)) {
        return false;
    }
    
    // Update Grassmann subspace
    update_subspace(analyzer);
    
    // Extract sector results
    extract_sector_results(analyzer);
    
    // Compute Leibniz-Bocker diagnostics
    compute_lb_diagnostics(analyzer);
    
    // Compute Grassmann curvature
    compute_grassmann_curvature(analyzer);
    
    // Calculate diffuseness
    analyzer->result.diffuseness = spatial_psmsl_calculate_diffuseness(analyzer);
    
    // Estimate DOA
    estimate_doa_internal(analyzer);
    
    // Update timestamp and frame count
    analyzer->result.timestamp_ms = analyzer->psmsl.result.timestamp_ms;
    analyzer->result.frame_count = analyzer->psmsl.frame_count;
    analyzer->result.valid = true;
    
    // Store in history
    memcpy(&analyzer->history[analyzer->history_index], 
           &analyzer->result, sizeof(spatial_psmsl_result_t));
    analyzer->history_index = (analyzer->history_index + 1) % SPATIAL_PSMSL_HISTORY_SIZE;
    
    return true;
}

const spatial_psmsl_result_t* spatial_psmsl_get_result(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return NULL;
    return &analyzer->result;
}

// =============================================================================
// Sector Access Functions
// =============================================================================

float spatial_psmsl_get_sector_energy(const spatial_psmsl_analyzer_t *analyzer, 
                                       uint8_t sector)
{
    if (!analyzer || sector >= SPATIAL_PSMSL_NUM_SECTORS) return -100.0f;
    return analyzer->result.sectors[sector].energy_db;
}

float spatial_psmsl_get_sector_coherence(const spatial_psmsl_analyzer_t *analyzer,
                                          uint8_t sector)
{
    if (!analyzer || sector >= SPATIAL_PSMSL_NUM_SECTORS) return 0.0f;
    return analyzer->result.sectors[sector].coherence;
}

float spatial_psmsl_get_sector_phi_weight(const spatial_psmsl_analyzer_t *analyzer,
                                           uint8_t sector)
{
    if (!analyzer || sector >= SPATIAL_PSMSL_NUM_SECTORS) return 0.0f;
    return analyzer->result.sectors[sector].phi_weight;
}

// =============================================================================
// Leibniz-Bocker Diagnostic Accessors
// =============================================================================

float spatial_psmsl_get_coherence(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    return analyzer->result.coherence;
}

float spatial_psmsl_get_curvature(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    return analyzer->result.curvature;
}

float spatial_psmsl_get_residual(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 1.0f;
    return analyzer->result.residual;
}

float spatial_psmsl_get_stability(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    return analyzer->result.stability;
}

float spatial_psmsl_get_novelty(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    return analyzer->result.novelty;
}

// =============================================================================
// Direction of Arrival Functions
// =============================================================================

bool spatial_psmsl_estimate_doa(const spatial_psmsl_analyzer_t *analyzer,
                                 spatial_doa_estimate_t *doa)
{
    if (!analyzer || !doa) return false;
    
    memcpy(doa, &analyzer->result.doa, sizeof(spatial_doa_estimate_t));
    return analyzer->result.doa.confidence > 0.3f;
}

const spatial_doa_estimate_t* spatial_psmsl_get_doa(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return NULL;
    return &analyzer->result.doa;
}

// =============================================================================
// Utility Functions
// =============================================================================

float spatial_psmsl_sector_to_freq(uint8_t sector)
{
    if (sector >= SPATIAL_PSMSL_NUM_SECTORS) return 0.0f;
    return sector_center_freq[sector];
}

uint8_t spatial_psmsl_freq_to_sector(float freq)
{
    for (uint8_t s = 0; s < SPATIAL_PSMSL_NUM_SECTORS; s++) {
        if (freq < PSMSL_SECTOR_FREQ_HIGH[s]) {
            return s;
        }
    }
    return SPATIAL_PSMSL_NUM_SECTORS - 1;
}

const char* spatial_psmsl_sector_name(uint8_t sector)
{
    if (sector >= SPATIAL_PSMSL_NUM_SECTORS) return "Unknown";
    return sector_names[sector];
}

float spatial_psmsl_calculate_diffuseness(const spatial_psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    
    // Diffuseness is inversely related to coherence
    // High coherence = directional sound = low diffuseness
    // Low coherence = diffuse sound = high diffuseness
    
    float avg_coherence = 0.0f;
    for (uint8_t s = 0; s < SPATIAL_PSMSL_NUM_SECTORS; s++) {
        avg_coherence += analyzer->result.sectors[s].coherence;
    }
    avg_coherence /= SPATIAL_PSMSL_NUM_SECTORS;
    
    return 1.0f - avg_coherence;
}
