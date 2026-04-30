/**
 * @file adaptation_controller_psmsl.c
 * @brief PSMSL-based adaptive crossover and room correction implementation
 * 
 * Uses Leibniz-Bocker diagnostics (Coherence, Curvature, Residual) for
 * optimization instead of FFT energy metrics.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "adaptation_controller_psmsl.h"
#include "psmsl_grassmann.h"
#include <string.h>
#include <math.h>
#include <stdio.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Default Configuration
// =============================================================================

static const psmsl_lb_targets_t default_lb_targets = {
    .target_coherence = 0.8f,
    .coherence_weight = 1.0f,
    .max_curvature = 0.2f,
    .curvature_weight = 0.5f,
    .max_residual = 0.3f,
    .residual_weight = 0.5f,
    .sector_coherence_target = {0.7f, 0.75f, 0.8f, 0.85f, 0.8f, 0.75f, 0.7f},
    .sector_energy_target = {-20.0f, -18.0f, -16.0f, -14.0f, -16.0f, -18.0f, -20.0f},
    .stability_threshold = 0.7f,
    .novelty_threshold = 0.3f,
};

static const psmsl_crossover_params_t default_crossover_params = {
    .adapt_crossover_freq = true,
    .crossover_freq_min = 40.0f,
    .crossover_freq_max = 120.0f,
    .crossover_freq_target = 80.0f,
    .adapt_sub_delay = true,
    .sub_delay_max_ms = 20.0f,
    .adapt_sub_phase = true,
    .adapt_sub_level = true,
    .sub_level_range_db = 6.0f,
    .adapt_main_delay = false,
    .main_delay_max_ms = 5.0f,
};

static const psmsl_correction_params_t default_correction_params = {
    .enable_peq = true,
    .max_peq_bands = 8,
    .max_cut_db = 12.0f,
    .max_boost_db = 6.0f,
    .min_q = 1.0f,
    .max_q = 10.0f,
    .use_sector_targets = true,
    .sector_target_db = {-20.0f, -18.0f, -16.0f, -14.0f, -16.0f, -18.0f, -20.0f},
    .coherence_weighted = true,
    .coherence_threshold = 0.5f,
    .correction_min_freq = 20.0f,
    .correction_max_freq = 500.0f,
};

// =============================================================================
// Private Functions
// =============================================================================

/**
 * @brief Update LB state from spatial analysis
 */
static void update_lb_state(psmsl_adaptation_controller_t *controller,
                            const spatial_psmsl_result_t *spatial)
{
    psmsl_lb_state_t *lb = &controller->state.lb_state;
    
    // Copy diagnostics
    lb->coherence = spatial->coherence;
    lb->curvature = spatial->curvature;
    lb->residual = spatial->residual;
    lb->stability = spatial->stability;
    lb->novelty = spatial->novelty;
    
    // Copy sector data
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        lb->sector_coherence[s] = spatial->sectors[s].coherence;
        lb->sector_energy[s] = spatial->sectors[s].energy_db;
    }
    
    // Compute cost function
    lb->cost_function = psmsl_adapt_compute_cost(controller);
    
    // Compute gradient magnitude from history
    if (controller->history_count >= 2) {
        float gradient[3];
        psmsl_adapt_compute_gradient(controller, gradient);
        lb->gradient_magnitude = sqrtf(gradient[0] * gradient[0] + 
                                        gradient[1] * gradient[1] + 
                                        gradient[2] * gradient[2]);
    } else {
        lb->gradient_magnitude = 1.0f;
    }
    
    // Grassmann manifold metrics
    lb->manifold_distance = spatial->grassmann_distance;
    lb->manifold_velocity = spatial->curvature;
}

/**
 * @brief Store current state in history
 */
static void update_history(psmsl_adaptation_controller_t *controller)
{
    psmsl_lb_state_t *lb = &controller->state.lb_state;
    
    controller->coherence_history[controller->history_index] = lb->coherence;
    controller->curvature_history[controller->history_index] = lb->curvature;
    controller->residual_history[controller->history_index] = lb->residual;
    controller->crossover_freq_history[controller->history_index] = 
        controller->state.current_crossover_freq;
    controller->sub_delay_history[controller->history_index] = 
        controller->state.current_sub_delay_ms;
    
    controller->history_index = (controller->history_index + 1) % PSMSL_ADAPT_HISTORY_SIZE;
    if (controller->history_count < PSMSL_ADAPT_HISTORY_SIZE) {
        controller->history_count++;
    }
}

/**
 * @brief Compute step size based on adaptation speed
 */
static float get_step_size(psmsl_adapt_speed_t speed)
{
    switch (speed) {
        case PSMSL_ADAPT_SPEED_SLOW:   return 0.01f;
        case PSMSL_ADAPT_SPEED_MEDIUM: return 0.05f;
        case PSMSL_ADAPT_SPEED_FAST:   return 0.1f;
        default:                        return 0.05f;
    }
}

/**
 * @brief Update crossover frequency based on LB diagnostics
 */
static void update_crossover_freq(psmsl_adaptation_controller_t *controller)
{
    if (!controller->crossover_params.adapt_crossover_freq) return;
    
    psmsl_lb_state_t *lb = &controller->state.lb_state;
    
    // Crossover optimization based on sector coherence
    // Goal: maximize coherence in Foundation and Structure sectors
    float low_coherence = (lb->sector_coherence[PSMSL_SECTOR_FOUNDATION] + 
                           lb->sector_coherence[PSMSL_SECTOR_STRUCTURE]) / 2.0f;
    
    float step = get_step_size(controller->state.speed);
    float current = controller->state.current_crossover_freq;
    
    // If low sector coherence is low, try adjusting crossover
    if (low_coherence < controller->lb_targets.sector_coherence_target[0]) {
        // Low coherence in bass = try moving crossover
        // Direction based on gradient
        float gradient = 0.0f;
        if (controller->history_count >= 2) {
            uint8_t prev_idx = (controller->history_index - 2 + PSMSL_ADAPT_HISTORY_SIZE) 
                               % PSMSL_ADAPT_HISTORY_SIZE;
            float prev_coherence = controller->coherence_history[prev_idx];
            float prev_freq = controller->crossover_freq_history[prev_idx];
            
            if (fabsf(prev_freq - current) > 0.1f) {
                gradient = (lb->coherence - prev_coherence) / (current - prev_freq);
            }
        }
        
        // Move in direction of increasing coherence
        float delta = step * 10.0f * (gradient > 0 ? 1.0f : -1.0f);
        current += delta;
    }
    
    // Clamp to limits
    if (current < controller->crossover_params.crossover_freq_min) {
        current = controller->crossover_params.crossover_freq_min;
    }
    if (current > controller->crossover_params.crossover_freq_max) {
        current = controller->crossover_params.crossover_freq_max;
    }
    
    controller->state.current_crossover_freq = current;
}

/**
 * @brief Update subwoofer delay based on LB diagnostics
 */
static void update_sub_delay(psmsl_adaptation_controller_t *controller)
{
    if (!controller->crossover_params.adapt_sub_delay) return;
    
    psmsl_lb_state_t *lb = &controller->state.lb_state;
    
    // Sub delay optimization: maximize coherence at crossover region
    // Structure sector (80-200 Hz) is the crossover region
    float xover_coherence = lb->sector_coherence[PSMSL_SECTOR_STRUCTURE];
    
    float step = get_step_size(controller->state.speed);
    float current = controller->state.current_sub_delay_ms;
    
    // If crossover coherence is low, adjust delay
    if (xover_coherence < controller->lb_targets.sector_coherence_target[1]) {
        // Try small delay adjustments
        float gradient = 0.0f;
        if (controller->history_count >= 2) {
            uint8_t prev_idx = (controller->history_index - 2 + PSMSL_ADAPT_HISTORY_SIZE) 
                               % PSMSL_ADAPT_HISTORY_SIZE;
            float prev_coherence = controller->coherence_history[prev_idx];
            float prev_delay = controller->sub_delay_history[prev_idx];
            
            if (fabsf(prev_delay - current) > 0.01f) {
                gradient = (lb->coherence - prev_coherence) / (current - prev_delay);
            }
        }
        
        float delta = step * 1.0f * (gradient > 0 ? 1.0f : -1.0f);
        current += delta;
    }
    
    // Clamp to limits
    if (current < 0.0f) current = 0.0f;
    if (current > controller->crossover_params.sub_delay_max_ms) {
        current = controller->crossover_params.sub_delay_max_ms;
    }
    
    controller->state.current_sub_delay_ms = current;
}

/**
 * @brief Update PEQ bands based on sector analysis
 */
static void update_peq_bands(psmsl_adaptation_controller_t *controller)
{
    if (!controller->correction_params.enable_peq) return;
    
    psmsl_lb_state_t *lb = &controller->state.lb_state;
    
    // Assign PEQ bands to sectors that need correction
    uint8_t band_idx = 0;
    
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS && 
         band_idx < controller->correction_params.max_peq_bands; s++) {
        
        float sector_freq = PSMSL_SECTOR_FREQ_LOW[s] + 
            (PSMSL_SECTOR_FREQ_HIGH[s] - PSMSL_SECTOR_FREQ_LOW[s]) / 2.0f;
        
        // Skip if outside correction range
        if (sector_freq < controller->correction_params.correction_min_freq ||
            sector_freq > controller->correction_params.correction_max_freq) {
            continue;
        }
        
        // Only correct if coherence is above threshold
        if (controller->correction_params.coherence_weighted &&
            lb->sector_coherence[s] < controller->correction_params.coherence_threshold) {
            continue;
        }
        
        // Calculate deviation from target
        float deviation = lb->sector_energy[s] - 
                          controller->correction_params.sector_target_db[s];
        
        // Only correct significant deviations
        if (fabsf(deviation) > 3.0f) {
            float gain = -deviation * 0.5f;  // Partial correction
            
            // Weight by coherence (more confident correction for higher coherence)
            if (controller->correction_params.coherence_weighted) {
                gain *= lb->sector_coherence[s];
            }
            
            // Clamp gain
            if (gain < -controller->correction_params.max_cut_db) {
                gain = -controller->correction_params.max_cut_db;
            }
            if (gain > controller->correction_params.max_boost_db) {
                gain = controller->correction_params.max_boost_db;
            }
            
            // Calculate Q based on sector bandwidth and coherence
            float bandwidth = PSMSL_SECTOR_FREQ_HIGH[s] - PSMSL_SECTOR_FREQ_LOW[s];
            float q = sector_freq / bandwidth;
            q *= (0.5f + 0.5f * lb->sector_coherence[s]);  // Narrower for higher coherence
            
            if (q < controller->correction_params.min_q) {
                q = controller->correction_params.min_q;
            }
            if (q > controller->correction_params.max_q) {
                q = controller->correction_params.max_q;
            }
            
            // Set PEQ band
            controller->state.peq_bands[band_idx].freq = sector_freq;
            controller->state.peq_bands[band_idx].gain_db = gain;
            controller->state.peq_bands[band_idx].q = q;
            controller->state.peq_bands[band_idx].active = true;
            controller->state.peq_bands[band_idx].target_sector = s;
            
            band_idx++;
        }
    }
    
    // Deactivate unused bands
    for (; band_idx < PSMSL_ADAPT_MAX_PEQ_BANDS; band_idx++) {
        controller->state.peq_bands[band_idx].active = false;
    }
    
    controller->state.active_peq_bands = band_idx;
}

/**
 * @brief Calculate quality metrics from LB state
 */
static void calculate_quality_metrics(psmsl_adaptation_controller_t *controller)
{
    psmsl_lb_state_t *lb = &controller->state.lb_state;
    
    // Bass evenness: variance of energy in low sectors
    float bass_mean = 0.0f;
    float bass_var = 0.0f;
    
    for (uint8_t s = 0; s <= PSMSL_SECTOR_BODY; s++) {
        bass_mean += lb->sector_energy[s];
    }
    bass_mean /= 3.0f;
    
    for (uint8_t s = 0; s <= PSMSL_SECTOR_BODY; s++) {
        float diff = lb->sector_energy[s] - bass_mean;
        bass_var += diff * diff;
    }
    bass_var /= 3.0f;
    
    controller->state.bass_evenness = 1.0f / (1.0f + sqrtf(bass_var) / 10.0f);
    
    // Integration quality: coherence at crossover region
    controller->state.integration_quality = lb->sector_coherence[PSMSL_SECTOR_STRUCTURE];
    
    // Overall correction: sum of PEQ gains
    float total_correction = 0.0f;
    for (uint8_t b = 0; b < controller->state.active_peq_bands; b++) {
        total_correction += fabsf(controller->state.peq_bands[b].gain_db);
    }
    controller->state.overall_correction = total_correction;
}

// =============================================================================
// Initialization Functions
// =============================================================================

bool psmsl_adapt_init(psmsl_adaptation_controller_t *controller,
                      audio_pipeline_t *pipeline,
                      spatial_psmsl_analyzer_t *spatial,
                      psmsl_mode_detector_t *mode_detector)
{
    if (!controller) return false;
    
    memset(controller, 0, sizeof(psmsl_adaptation_controller_t));
    
    // Set references
    controller->pipeline = pipeline;
    controller->spatial = spatial;
    controller->mode_detector = mode_detector;
    
    // Set defaults
    memcpy(&controller->lb_targets, &default_lb_targets, sizeof(psmsl_lb_targets_t));
    memcpy(&controller->crossover_params, &default_crossover_params, 
           sizeof(psmsl_crossover_params_t));
    memcpy(&controller->correction_params, &default_correction_params, 
           sizeof(psmsl_correction_params_t));
    
    // Initialize state
    controller->state.mode = PSMSL_ADAPT_MODE_OFF;
    controller->state.speed = PSMSL_ADAPT_SPEED_MEDIUM;
    controller->state.current_crossover_freq = 80.0f;
    controller->state.current_sub_delay_ms = 0.0f;
    controller->state.current_sub_phase_deg = 0.0f;
    controller->state.current_sub_level_db = 0.0f;
    controller->state.current_main_delay_ms = 0.0f;
    
    // Timing
    controller->update_interval_ms = 1000 / PSMSL_ADAPT_UPDATE_RATE_HZ;
    
    controller->initialized = true;
    
    return true;
}

void psmsl_adapt_reset(psmsl_adaptation_controller_t *controller)
{
    if (!controller) return;
    
    memset(&controller->state, 0, sizeof(psmsl_adapt_state_t));
    memset(controller->coherence_history, 0, sizeof(controller->coherence_history));
    memset(controller->curvature_history, 0, sizeof(controller->curvature_history));
    memset(controller->residual_history, 0, sizeof(controller->residual_history));
    memset(controller->crossover_freq_history, 0, sizeof(controller->crossover_freq_history));
    memset(controller->sub_delay_history, 0, sizeof(controller->sub_delay_history));
    
    controller->history_index = 0;
    controller->history_count = 0;
    controller->has_target_subspace = false;
    
    controller->state.current_crossover_freq = 80.0f;
}

void psmsl_adapt_set_lb_targets(psmsl_adaptation_controller_t *controller,
                                 const psmsl_lb_targets_t *targets)
{
    if (!controller || !targets) return;
    memcpy(&controller->lb_targets, targets, sizeof(psmsl_lb_targets_t));
}

void psmsl_adapt_set_crossover_params(psmsl_adaptation_controller_t *controller,
                                       const psmsl_crossover_params_t *params)
{
    if (!controller || !params) return;
    memcpy(&controller->crossover_params, params, sizeof(psmsl_crossover_params_t));
}

void psmsl_adapt_set_correction_params(psmsl_adaptation_controller_t *controller,
                                        const psmsl_correction_params_t *params)
{
    if (!controller || !params) return;
    memcpy(&controller->correction_params, params, sizeof(psmsl_correction_params_t));
}

// =============================================================================
// Control Functions
// =============================================================================

void psmsl_adapt_set_mode(psmsl_adaptation_controller_t *controller, 
                          psmsl_adapt_mode_t mode)
{
    if (!controller) return;
    controller->state.mode = mode;
    
    if (mode == PSMSL_ADAPT_MODE_ADAPTIVE) {
        controller->running = true;
    } else if (mode == PSMSL_ADAPT_MODE_OFF || mode == PSMSL_ADAPT_MODE_HOLD) {
        controller->running = false;
    }
}

void psmsl_adapt_set_speed(psmsl_adaptation_controller_t *controller, 
                           psmsl_adapt_speed_t speed)
{
    if (!controller) return;
    controller->state.speed = speed;
}

bool psmsl_adapt_start_calibration(psmsl_adaptation_controller_t *controller)
{
    if (!controller || !controller->initialized) return false;
    
    psmsl_adapt_reset(controller);
    controller->state.mode = PSMSL_ADAPT_MODE_CALIBRATE;
    controller->running = true;
    
    return true;
}

bool psmsl_adapt_start_adaptive(psmsl_adaptation_controller_t *controller)
{
    if (!controller || !controller->initialized) return false;
    
    controller->state.mode = PSMSL_ADAPT_MODE_ADAPTIVE;
    controller->running = true;
    
    return true;
}

void psmsl_adapt_stop(psmsl_adaptation_controller_t *controller)
{
    if (!controller) return;
    
    controller->state.mode = PSMSL_ADAPT_MODE_HOLD;
    controller->running = false;
}

// =============================================================================
// Processing Functions
// =============================================================================

bool psmsl_adapt_update(psmsl_adaptation_controller_t *controller)
{
    if (!controller || !controller->initialized || !controller->running) {
        return false;
    }
    
    // Check if it's time to update
    // (In real implementation, check against system time)
    
    if (controller->state.mode == PSMSL_ADAPT_MODE_OFF ||
        controller->state.mode == PSMSL_ADAPT_MODE_HOLD) {
        return false;
    }
    
    // Update parameters based on LB diagnostics
    update_crossover_freq(controller);
    update_sub_delay(controller);
    update_peq_bands(controller);
    
    // Calculate quality metrics
    calculate_quality_metrics(controller);
    
    // Check convergence
    controller->state.converged = psmsl_adapt_check_convergence(controller);
    controller->state.convergence = psmsl_adapt_get_convergence(controller);
    
    // Update history
    update_history(controller);
    
    controller->state.iterations++;
    
    return true;
}

void psmsl_adapt_process_spatial(psmsl_adaptation_controller_t *controller,
                                  const spatial_psmsl_result_t *spatial)
{
    if (!controller || !spatial || !spatial->valid) return;
    
    // Update LB state from spatial analysis
    update_lb_state(controller, spatial);
    
    controller->state.timestamp_ms = spatial->timestamp_ms;
    controller->state.frame_count = spatial->frame_count;
}

void psmsl_adapt_process_modes(psmsl_adaptation_controller_t *controller,
                                const psmsl_mode_detector_result_t *modes)
{
    if (!controller || !modes || !modes->valid) return;
    
    // Use mode information to refine PEQ targeting
    // (Additional mode-specific optimization could be added here)
}

// =============================================================================
// Leibniz-Bocker Optimization Functions
// =============================================================================

float psmsl_adapt_compute_cost(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return 1.0f;
    
    const psmsl_lb_state_t *lb = &controller->state.lb_state;
    const psmsl_lb_targets_t *targets = &controller->lb_targets;
    
    // Cost = w_c * (1 - coherence) + w_k * curvature + w_r * residual
    float coherence_cost = (1.0f - lb->coherence) * targets->coherence_weight;
    float curvature_cost = lb->curvature * targets->curvature_weight;
    float residual_cost = lb->residual * targets->residual_weight;
    
    return coherence_cost + curvature_cost + residual_cost;
}

void psmsl_adapt_compute_gradient(const psmsl_adaptation_controller_t *controller,
                                   float gradient[3])
{
    if (!controller || !gradient) return;
    
    gradient[0] = 0.0f;
    gradient[1] = 0.0f;
    gradient[2] = 0.0f;
    
    if (controller->history_count < 2) return;
    
    // Compute gradient from history
    uint8_t curr_idx = (controller->history_index - 1 + PSMSL_ADAPT_HISTORY_SIZE) 
                       % PSMSL_ADAPT_HISTORY_SIZE;
    uint8_t prev_idx = (controller->history_index - 2 + PSMSL_ADAPT_HISTORY_SIZE) 
                       % PSMSL_ADAPT_HISTORY_SIZE;
    
    gradient[0] = controller->coherence_history[curr_idx] - 
                  controller->coherence_history[prev_idx];
    gradient[1] = controller->curvature_history[curr_idx] - 
                  controller->curvature_history[prev_idx];
    gradient[2] = controller->residual_history[curr_idx] - 
                  controller->residual_history[prev_idx];
}

bool psmsl_adapt_optimization_step(psmsl_adaptation_controller_t *controller,
                                    float step_size)
{
    if (!controller) return false;
    
    // This is called internally by psmsl_adapt_update
    // The actual parameter updates are done in update_crossover_freq, etc.
    
    return true;
}

bool psmsl_adapt_check_convergence(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return false;
    
    const psmsl_lb_state_t *lb = &controller->state.lb_state;
    const psmsl_lb_targets_t *targets = &controller->lb_targets;
    
    // Check all convergence criteria
    bool coherence_ok = lb->coherence >= targets->target_coherence;
    bool curvature_ok = lb->curvature <= targets->max_curvature;
    bool residual_ok = lb->residual <= targets->max_residual;
    bool gradient_ok = lb->gradient_magnitude < 0.01f;
    
    return coherence_ok && curvature_ok && residual_ok && gradient_ok;
}

// =============================================================================
// State Query Functions
// =============================================================================

const psmsl_adapt_state_t* psmsl_adapt_get_state(
    const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return NULL;
    return &controller->state;
}

const psmsl_lb_state_t* psmsl_adapt_get_lb_state(
    const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return NULL;
    return &controller->state.lb_state;
}

float psmsl_adapt_get_coherence(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return 0.0f;
    return controller->state.lb_state.coherence;
}

float psmsl_adapt_get_curvature(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return 0.0f;
    return controller->state.lb_state.curvature;
}

float psmsl_adapt_get_residual(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return 1.0f;
    return controller->state.lb_state.residual;
}

bool psmsl_adapt_is_converged(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return false;
    return controller->state.converged;
}

float psmsl_adapt_get_convergence(const psmsl_adaptation_controller_t *controller)
{
    if (!controller) return 0.0f;
    
    const psmsl_lb_state_t *lb = &controller->state.lb_state;
    const psmsl_lb_targets_t *targets = &controller->lb_targets;
    
    // Convergence is weighted average of how close each metric is to target
    float coherence_progress = lb->coherence / targets->target_coherence;
    if (coherence_progress > 1.0f) coherence_progress = 1.0f;
    
    float curvature_progress = 1.0f - (lb->curvature / targets->max_curvature);
    if (curvature_progress < 0.0f) curvature_progress = 0.0f;
    
    float residual_progress = 1.0f - (lb->residual / targets->max_residual);
    if (residual_progress < 0.0f) residual_progress = 0.0f;
    
    return (coherence_progress + curvature_progress + residual_progress) / 3.0f;
}

// =============================================================================
// Manual Override Functions
// =============================================================================

void psmsl_adapt_set_crossover_freq(psmsl_adaptation_controller_t *controller, 
                                     float freq)
{
    if (!controller) return;
    controller->state.current_crossover_freq = freq;
}

void psmsl_adapt_set_sub_delay(psmsl_adaptation_controller_t *controller, 
                                float delay_ms)
{
    if (!controller) return;
    controller->state.current_sub_delay_ms = delay_ms;
}

void psmsl_adapt_set_sub_level(psmsl_adaptation_controller_t *controller, 
                                float level_db)
{
    if (!controller) return;
    controller->state.current_sub_level_db = level_db;
}

void psmsl_adapt_set_peq_band(psmsl_adaptation_controller_t *controller,
                               uint8_t band, float freq, float gain_db, 
                               float q, bool active)
{
    if (!controller || band >= PSMSL_ADAPT_MAX_PEQ_BANDS) return;
    
    controller->state.peq_bands[band].freq = freq;
    controller->state.peq_bands[band].gain_db = gain_db;
    controller->state.peq_bands[band].q = q;
    controller->state.peq_bands[band].active = active;
}

// =============================================================================
// Preset Functions
// =============================================================================

bool psmsl_adapt_save_preset(psmsl_adaptation_controller_t *controller, 
                              const char *name)
{
    // TODO: Implement preset saving to NVS
    (void)controller;
    (void)name;
    return true;
}

bool psmsl_adapt_load_preset(psmsl_adaptation_controller_t *controller, 
                              const char *name)
{
    // TODO: Implement preset loading from NVS
    (void)controller;
    (void)name;
    return true;
}

int psmsl_adapt_export_json(const psmsl_adaptation_controller_t *controller,
                             char *buffer, size_t buffer_size)
{
    if (!controller || !buffer || buffer_size == 0) return 0;
    
    const psmsl_adapt_state_t *state = &controller->state;
    
    int len = snprintf(buffer, buffer_size,
        "{\n"
        "  \"crossover_freq\": %.1f,\n"
        "  \"sub_delay_ms\": %.2f,\n"
        "  \"sub_level_db\": %.1f,\n"
        "  \"coherence\": %.3f,\n"
        "  \"curvature\": %.3f,\n"
        "  \"residual\": %.3f,\n"
        "  \"convergence\": %.3f,\n"
        "  \"converged\": %s\n"
        "}\n",
        state->current_crossover_freq,
        state->current_sub_delay_ms,
        state->current_sub_level_db,
        state->lb_state.coherence,
        state->lb_state.curvature,
        state->lb_state.residual,
        state->convergence,
        state->converged ? "true" : "false"
    );
    
    return len;
}

bool psmsl_adapt_import_json(psmsl_adaptation_controller_t *controller, 
                              const char *json)
{
    // TODO: Implement JSON parsing
    (void)controller;
    (void)json;
    return true;
}
