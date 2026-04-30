/**
 * @file room_mode_detector_psmsl.c
 * @brief PSMSL-based room acoustic mode detection implementation
 * 
 * Uses Leibniz-Bocker diagnostics (Coherence, Curvature, Residual)
 * for room mode detection instead of FFT peak analysis.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "room_mode_detector_psmsl.h"
#include "psmsl_grassmann.h"
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Default Thresholds
// =============================================================================

#define DEFAULT_COHERENCE_THRESHOLD     0.6f    // Minimum coherence for mode
#define DEFAULT_CURVATURE_THRESHOLD     0.3f    // Maximum curvature for stable mode
#define DEFAULT_RESIDUAL_THRESHOLD      0.4f    // Maximum residual for known mode

// =============================================================================
// Private Functions
// =============================================================================

/**
 * @brief Detect modes using Leibniz-Bocker coherence analysis
 * 
 * A mode is detected when:
 * - Coherence > threshold (structured resonance)
 * - Curvature < threshold (stable over time)
 * - Residual < threshold (not novel/transient)
 */
static void detect_modes_lb(psmsl_mode_detector_t *detector,
                            const psmsl_result_t *psmsl)
{
    psmsl_mode_detector_result_t *result = &detector->result;
    
    // Clear previous modes
    result->num_modes = 0;
    
    // Analyze each sector for potential modes
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        const psmsl_sector_result_t *sector = &psmsl->sectors[s];
        
        // Check if sector has mode-like characteristics
        bool has_high_coherence = sector->sector_coherence > detector->coherence_threshold;
        bool has_significant_energy = sector->energy_db > -60.0f;
        
        if (has_high_coherence && has_significant_energy) {
            // Potential mode detected
            if (result->num_modes < PSMSL_MAX_ROOM_MODES) {
                psmsl_room_mode_t *mode = &result->modes[result->num_modes];
                
                // Frequency from sector center
                mode->frequency = PSMSL_SECTOR_FREQ_LOW[s] + 
                    (PSMSL_SECTOR_FREQ_HIGH[s] - PSMSL_SECTOR_FREQ_LOW[s]) / 2.0f;
                mode->bandwidth = PSMSL_SECTOR_FREQ_HIGH[s] - PSMSL_SECTOR_FREQ_LOW[s];
                mode->q_factor = mode->frequency / mode->bandwidth;
                mode->magnitude_db = sector->energy_db;
                
                // Estimate decay time from coherence
                // High coherence = longer decay (more ringing)
                mode->decay_time_ms = 100.0f + 400.0f * sector->sector_coherence;
                
                // Classify mode type based on sector
                if (s <= SPATIAL_SECTOR_STRUCTURE) {
                    mode->type = PSMSL_MODE_TYPE_AXIAL;  // Low freq = axial
                } else if (s <= SPATIAL_SECTOR_BODY) {
                    mode->type = PSMSL_MODE_TYPE_TANGENTIAL;
                } else {
                    mode->type = PSMSL_MODE_TYPE_OBLIQUE;
                }
                
                // Semantic sector mapping
                mode->primary_sector = s;
                for (uint8_t i = 0; i < PSMSL_NUM_SECTORS; i++) {
                    mode->sector_energy[i] = psmsl->sectors[i].energy_linear;
                }
                
                // Leibniz-Bocker state for this mode
                mode->lb_state.coherence = sector->sector_coherence;
                mode->lb_state.curvature = psmsl->diagnostics.curvature;
                mode->lb_state.residual = psmsl->diagnostics.residual;
                mode->lb_state.stability = 1.0f / (1.0f + mode->lb_state.curvature);
                mode->lb_state.trajectory_length = 0.0f;  // Updated over time
                
                // Spatial coherence
                mode->spatial_coherence = sector->sector_coherence;
                mode->nodal_positions = 0;  // Would need mic-level data
                
                // Correction suggestion
                psmsl_mode_detector_suggest_peq(mode,
                    &mode->suggested_eq_freq,
                    &mode->suggested_eq_gain,
                    &mode->suggested_eq_q);
                
                // Tracking state
                mode->active = true;
                mode->persistence = 1;
                mode->confidence = sector->sector_coherence;
                mode->grassmann_distance = 0.0f;
                
                result->num_modes++;
            }
        }
        
        // Store sector analysis
        result->sector_energy[s] = sector->energy_db;
        result->sector_coherence[s] = sector->sector_coherence;
    }
}

/**
 * @brief Update mode tracking with temporal history
 */
static void update_mode_tracking(psmsl_mode_detector_t *detector)
{
    psmsl_mode_detector_result_t *result = &detector->result;
    
    // Match current modes with history
    for (uint8_t m = 0; m < result->num_modes; m++) {
        psmsl_room_mode_t *mode = &result->modes[m];
        
        // Look for matching mode in history
        // (simplified: match by sector)
        uint8_t sector = mode->primary_sector;
        
        // Check coherence history for this sector
        float coherence_avg = 0.0f;
        uint32_t count = 0;
        
        for (uint32_t h = 0; h < detector->history_count && h < PSMSL_MODE_HISTORY; h++) {
            uint8_t idx = (detector->history_index - 1 - h + PSMSL_MODE_HISTORY) % PSMSL_MODE_HISTORY;
            coherence_avg += detector->sector_history[idx][sector];
            count++;
        }
        
        if (count > 0) {
            coherence_avg /= count;
            
            // Mode is persistent if coherence is consistently high
            if (coherence_avg > detector->coherence_threshold * 0.8f) {
                mode->persistence = count;
                mode->confidence = coherence_avg;
            }
        }
    }
}

/**
 * @brief Calculate room quality metrics
 */
static void calculate_quality_metrics(psmsl_mode_detector_t *detector,
                                       const psmsl_result_t *psmsl)
{
    psmsl_mode_detector_result_t *result = &detector->result;
    
    // Bass evenness: variance of energy in low sectors
    float bass_mean = 0.0f;
    float bass_var = 0.0f;
    
    for (uint8_t s = 0; s <= SPATIAL_SECTOR_BODY; s++) {
        bass_mean += result->sector_energy[s];
    }
    bass_mean /= 3.0f;
    
    for (uint8_t s = 0; s <= SPATIAL_SECTOR_BODY; s++) {
        float diff = result->sector_energy[s] - bass_mean;
        bass_var += diff * diff;
    }
    bass_var /= 3.0f;
    
    // Low variance = even bass
    result->bass_evenness = 1.0f / (1.0f + sqrtf(bass_var) / 10.0f);
    
    // Modal ringing: based on coherence in low sectors
    float ringing = 0.0f;
    for (uint8_t s = 0; s <= SPATIAL_SECTOR_BODY; s++) {
        ringing += result->sector_coherence[s];
    }
    result->modal_ringing = ringing / 3.0f;
    
    // Correction urgency: combination of unevenness and ringing
    result->correction_urgency = (1.0f - result->bass_evenness) * 0.5f + 
                                  result->modal_ringing * 0.5f;
    
    // Manifold metrics from PSMSL
    result->manifold_velocity = psmsl->diagnostics.curvature;
    result->manifold_curvature = psmsl->diagnostics.curvature;  // Simplified
}

/**
 * @brief Store current state in history
 */
static void update_history(psmsl_mode_detector_t *detector,
                           const psmsl_result_t *psmsl)
{
    // Store sector energies
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        detector->sector_history[detector->history_index][s] = 
            psmsl->sectors[s].sector_coherence;
    }
    
    // Store global diagnostics
    detector->coherence_history[detector->history_index] = psmsl->diagnostics.coherence;
    detector->curvature_history[detector->history_index] = psmsl->diagnostics.curvature;
    
    // Advance history index
    detector->history_index = (detector->history_index + 1) % PSMSL_MODE_HISTORY;
    if (detector->history_count < PSMSL_MODE_HISTORY) {
        detector->history_count++;
    }
}

// =============================================================================
// Initialization Functions
// =============================================================================

bool psmsl_mode_detector_init(psmsl_mode_detector_t *detector, float sample_rate)
{
    if (!detector) return false;
    
    memset(detector, 0, sizeof(psmsl_mode_detector_t));
    
    detector->sample_rate = sample_rate;
    detector->speed_of_sound = 343.0f;
    
    // Set default thresholds
    detector->coherence_threshold = DEFAULT_COHERENCE_THRESHOLD;
    detector->curvature_threshold = DEFAULT_CURVATURE_THRESHOLD;
    detector->residual_threshold = DEFAULT_RESIDUAL_THRESHOLD;
    
    detector->initialized = true;
    
    return true;
}

void psmsl_mode_detector_reset(psmsl_mode_detector_t *detector)
{
    if (!detector) return;
    
    memset(&detector->result, 0, sizeof(psmsl_mode_detector_result_t));
    memset(detector->sector_history, 0, sizeof(detector->sector_history));
    memset(detector->coherence_history, 0, sizeof(detector->coherence_history));
    memset(detector->curvature_history, 0, sizeof(detector->curvature_history));
    
    detector->history_index = 0;
    detector->history_count = 0;
}

void psmsl_mode_detector_set_dimensions(psmsl_mode_detector_t *detector,
                                         float length, float width, float height)
{
    if (!detector) return;
    
    detector->result.dimensions.length = length;
    detector->result.dimensions.width = width;
    detector->result.dimensions.height = height;
    detector->result.dimensions.confidence = 1.0f;
    detector->dimensions_known = true;
    
    // Calculate Schroeder frequency
    float volume = length * width * height;
    float surface = 2.0f * (length * width + width * height + height * length);
    float rt60_estimate = 0.161f * volume / (surface * 0.1f);  // Assume α = 0.1
    
    detector->result.rt60_estimate = rt60_estimate;
    detector->result.schroeder_freq = 2000.0f * sqrtf(rt60_estimate / volume);
}

void psmsl_mode_detector_set_thresholds(psmsl_mode_detector_t *detector,
                                         float coherence_threshold,
                                         float curvature_threshold,
                                         float residual_threshold)
{
    if (!detector) return;
    
    detector->coherence_threshold = coherence_threshold;
    detector->curvature_threshold = curvature_threshold;
    detector->residual_threshold = residual_threshold;
}

// =============================================================================
// Detection Functions
// =============================================================================

bool psmsl_mode_detector_process(psmsl_mode_detector_t *detector,
                                  const spatial_psmsl_result_t *spatial)
{
    if (!detector || !detector->initialized || !spatial || !spatial->valid) {
        return false;
    }
    
    // Convert spatial result to PSMSL format
    // (In practice, we'd have direct access to the PSMSL result)
    psmsl_result_t psmsl_equiv;
    memset(&psmsl_equiv, 0, sizeof(psmsl_equiv));
    
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        psmsl_equiv.sectors[s].energy_linear = spatial->sectors[s].energy_linear;
        psmsl_equiv.sectors[s].energy_db = spatial->sectors[s].energy_db;
        psmsl_equiv.sectors[s].sector_coherence = spatial->sectors[s].coherence;
        psmsl_equiv.sectors[s].phase = spatial->sectors[s].phase;
        psmsl_equiv.sectors[s].phi_weight = spatial->sectors[s].phi_weight;
        psmsl_equiv.sectors[s].eigenvalue_ratio = spatial->sectors[s].eigenvalue_ratio;
    }
    
    psmsl_equiv.diagnostics.coherence = spatial->coherence;
    psmsl_equiv.diagnostics.curvature = spatial->curvature;
    psmsl_equiv.diagnostics.residual = spatial->residual;
    psmsl_equiv.diagnostics.stability = spatial->stability;
    psmsl_equiv.diagnostics.novelty = spatial->novelty;
    psmsl_equiv.valid = true;
    
    return psmsl_mode_detector_process_psmsl(detector, &psmsl_equiv);
}

bool psmsl_mode_detector_process_psmsl(psmsl_mode_detector_t *detector,
                                        const psmsl_result_t *psmsl)
{
    if (!detector || !detector->initialized || !psmsl || !psmsl->valid) {
        return false;
    }
    
    // Store global diagnostics
    detector->result.global_coherence = psmsl->diagnostics.coherence;
    detector->result.global_curvature = psmsl->diagnostics.curvature;
    detector->result.global_residual = psmsl->diagnostics.residual;
    
    // Detect modes using Leibniz-Bocker analysis
    detect_modes_lb(detector, psmsl);
    
    // Update mode tracking with history
    update_mode_tracking(detector);
    
    // Calculate quality metrics
    calculate_quality_metrics(detector, psmsl);
    
    // Update history
    update_history(detector, psmsl);
    
    // Update result metadata
    detector->result.timestamp_ms = psmsl->timestamp_ms;
    detector->result.frame_count = psmsl->frame_count;
    detector->result.valid = true;
    
    return true;
}

const psmsl_mode_detector_result_t* psmsl_mode_detector_get_result(
    const psmsl_mode_detector_t *detector)
{
    if (!detector) return NULL;
    return &detector->result;
}

// =============================================================================
// Mode Query Functions
// =============================================================================

uint8_t psmsl_mode_detector_get_mode_count(const psmsl_mode_detector_t *detector)
{
    if (!detector) return 0;
    return detector->result.num_modes;
}

const psmsl_room_mode_t* psmsl_mode_detector_get_mode(
    const psmsl_mode_detector_t *detector, uint8_t index)
{
    if (!detector || index >= detector->result.num_modes) return NULL;
    return &detector->result.modes[index];
}

const psmsl_room_mode_t* psmsl_mode_detector_find_mode_in_sector(
    const psmsl_mode_detector_t *detector, uint8_t sector)
{
    if (!detector || sector >= PSMSL_NUM_SECTORS) return NULL;
    
    for (uint8_t m = 0; m < detector->result.num_modes; m++) {
        if (detector->result.modes[m].primary_sector == sector) {
            return &detector->result.modes[m];
        }
    }
    return NULL;
}

const psmsl_room_mode_t* psmsl_mode_detector_get_worst_mode(
    const psmsl_mode_detector_t *detector)
{
    if (!detector || detector->result.num_modes == 0) return NULL;
    
    const psmsl_room_mode_t *worst = NULL;
    float worst_score = 0.0f;
    
    for (uint8_t m = 0; m < detector->result.num_modes; m++) {
        const psmsl_room_mode_t *mode = &detector->result.modes[m];
        
        // Score: high coherence + high magnitude = problematic
        float score = mode->lb_state.coherence * 
                      (1.0f + mode->magnitude_db / 20.0f);
        
        if (score > worst_score) {
            worst_score = score;
            worst = mode;
        }
    }
    
    return worst;
}

const psmsl_room_mode_t* psmsl_mode_detector_get_most_stable_mode(
    const psmsl_mode_detector_t *detector)
{
    if (!detector || detector->result.num_modes == 0) return NULL;
    
    const psmsl_room_mode_t *stable = NULL;
    float best_stability = 0.0f;
    
    for (uint8_t m = 0; m < detector->result.num_modes; m++) {
        const psmsl_room_mode_t *mode = &detector->result.modes[m];
        
        if (mode->lb_state.stability > best_stability) {
            best_stability = mode->lb_state.stability;
            stable = mode;
        }
    }
    
    return stable;
}

// =============================================================================
// Leibniz-Bocker Diagnostic Queries
// =============================================================================

float psmsl_mode_detector_get_coherence(const psmsl_mode_detector_t *detector)
{
    if (!detector) return 0.0f;
    return detector->result.global_coherence;
}

float psmsl_mode_detector_get_curvature(const psmsl_mode_detector_t *detector)
{
    if (!detector) return 0.0f;
    return detector->result.global_curvature;
}

float psmsl_mode_detector_get_residual(const psmsl_mode_detector_t *detector)
{
    if (!detector) return 1.0f;
    return detector->result.global_residual;
}

float psmsl_mode_detector_get_sector_coherence(
    const psmsl_mode_detector_t *detector, uint8_t sector)
{
    if (!detector || sector >= PSMSL_NUM_SECTORS) return 0.0f;
    return detector->result.sector_coherence[sector];
}

// =============================================================================
// Correction Suggestion Functions
// =============================================================================

void psmsl_mode_detector_suggest_peq(const psmsl_room_mode_t *mode,
                                      float *freq, float *gain_db, float *q)
{
    if (!mode || !freq || !gain_db || !q) return;
    
    *freq = mode->frequency;
    
    // Gain based on magnitude and coherence
    // High coherence = more aggressive correction
    float correction_factor = mode->lb_state.coherence;
    *gain_db = -mode->magnitude_db * correction_factor * 0.5f;
    
    // Clamp gain
    if (*gain_db < -12.0f) *gain_db = -12.0f;
    if (*gain_db > 0.0f) *gain_db = 0.0f;
    
    // Q based on mode Q and stability
    // Stable modes need narrower correction
    *q = mode->q_factor * mode->lb_state.stability;
    
    // Clamp Q
    if (*q < 1.0f) *q = 1.0f;
    if (*q > 10.0f) *q = 10.0f;
}

void psmsl_mode_detector_generate_correction(
    const psmsl_mode_detector_t *detector,
    float correction_db[PSMSL_NUM_SECTORS],
    float max_cut_db,
    float max_boost_db)
{
    if (!detector || !correction_db) return;
    
    // Calculate target curve based on sector analysis
    float target_energy = 0.0f;
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        target_energy += detector->result.sector_energy[s];
    }
    target_energy /= PSMSL_NUM_SECTORS;
    
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        float deviation = detector->result.sector_energy[s] - target_energy;
        
        // Weight by coherence (correct more where coherence is high)
        float weight = detector->result.sector_coherence[s];
        
        correction_db[s] = -deviation * weight * 0.5f;
        
        // Clamp
        if (correction_db[s] < -max_cut_db) correction_db[s] = -max_cut_db;
        if (correction_db[s] > max_boost_db) correction_db[s] = max_boost_db;
    }
}

// =============================================================================
// Room Analysis Functions
// =============================================================================

bool psmsl_mode_detector_estimate_dimensions(
    const psmsl_mode_detector_t *detector,
    psmsl_room_dimensions_t *dimensions)
{
    if (!detector || !dimensions) return false;
    
    if (detector->dimensions_known) {
        memcpy(dimensions, &detector->result.dimensions, sizeof(psmsl_room_dimensions_t));
        return true;
    }
    
    // Estimate from detected modes
    // Axial modes: f = c / (2 * L)
    // So L = c / (2 * f)
    
    float c = detector->speed_of_sound;
    float estimated_dims[3] = {0.0f, 0.0f, 0.0f};
    uint8_t dim_count = 0;
    
    for (uint8_t m = 0; m < detector->result.num_modes && dim_count < 3; m++) {
        const psmsl_room_mode_t *mode = &detector->result.modes[m];
        
        if (mode->type == PSMSL_MODE_TYPE_AXIAL && mode->confidence > 0.7f) {
            float dim = c / (2.0f * mode->frequency);
            estimated_dims[dim_count++] = dim;
        }
    }
    
    if (dim_count >= 1) {
        // Sort dimensions (largest first)
        for (uint8_t i = 0; i < dim_count - 1; i++) {
            for (uint8_t j = i + 1; j < dim_count; j++) {
                if (estimated_dims[j] > estimated_dims[i]) {
                    float temp = estimated_dims[i];
                    estimated_dims[i] = estimated_dims[j];
                    estimated_dims[j] = temp;
                }
            }
        }
        
        dimensions->length = estimated_dims[0];
        dimensions->width = (dim_count >= 2) ? estimated_dims[1] : estimated_dims[0] * 0.7f;
        dimensions->height = (dim_count >= 3) ? estimated_dims[2] : 2.5f;
        dimensions->confidence = 0.3f + 0.2f * dim_count;
        
        return true;
    }
    
    return false;
}

float psmsl_mode_detector_get_schroeder_freq(const psmsl_mode_detector_t *detector)
{
    if (!detector) return 200.0f;
    
    if (detector->result.schroeder_freq > 0.0f) {
        return detector->result.schroeder_freq;
    }
    
    // Estimate from RT60 and assumed volume
    float rt60 = detector->result.rt60_estimate;
    if (rt60 <= 0.0f) rt60 = 0.5f;  // Default
    
    float volume = 50.0f;  // Assume 50 m³ if unknown
    if (detector->dimensions_known) {
        volume = detector->result.dimensions.length *
                 detector->result.dimensions.width *
                 detector->result.dimensions.height;
    }
    
    return 2000.0f * sqrtf(rt60 / volume);
}

float psmsl_mode_detector_get_sector_modal_density(
    const psmsl_mode_detector_t *detector, uint8_t sector)
{
    if (!detector || sector >= PSMSL_NUM_SECTORS) return 0.0f;
    
    // Count modes in this sector
    float count = 0.0f;
    for (uint8_t m = 0; m < detector->result.num_modes; m++) {
        if (detector->result.modes[m].primary_sector == sector) {
            count += 1.0f;
        }
    }
    
    // Divide by sector bandwidth
    float bandwidth = PSMSL_SECTOR_FREQ_HIGH[sector] - PSMSL_SECTOR_FREQ_LOW[sector];
    
    return count / bandwidth;
}
