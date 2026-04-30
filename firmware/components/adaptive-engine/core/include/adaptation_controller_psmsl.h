/**
 * @file adaptation_controller_psmsl.h
 * @brief PSMSL-based adaptive crossover and room correction controller
 * 
 * Replaces FFT energy optimization with Leibniz-Bocker diagnostic
 * optimization (Coherence, Curvature, Residual). The controller
 * tracks trajectories on the Grassmann manifold to achieve stable,
 * optimal acoustic response.
 * 
 * Optimization Targets:
 * - Maximize Coherence (ρ): Structured, well-defined sound field
 * - Minimize Curvature (Ω): Stable, non-fluctuating parameters
 * - Minimize Residual (r): Low unexplained variance / novelty
 * 
 * Theoretical Foundation:
 * - Leibniz-Bocker Framework: Covariance geometry for optimization
 * - Grassmann Manifold: Eigenspace trajectories for convergence
 * - Thyme Identity: 7 semantic sectors for frequency organization
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef ADAPTATION_CONTROLLER_PSMSL_H
#define ADAPTATION_CONTROLLER_PSMSL_H

#include <stdint.h>
#include <stdbool.h>
#include "audio_pipeline.h"
#include "spatial_decomposition_psmsl.h"
#include "room_mode_detector_psmsl.h"
#include "psmsl_analysis.h"

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

#define PSMSL_ADAPT_MAX_PEQ_BANDS   10      // Maximum PEQ bands
#define PSMSL_ADAPT_HISTORY_SIZE    64      // Parameter history
#define PSMSL_ADAPT_UPDATE_RATE_HZ  10      // Target update rate

// =============================================================================
// Types
// =============================================================================

/**
 * @brief Adaptation mode (preserved from original)
 */
typedef enum {
    PSMSL_ADAPT_MODE_OFF,           // No adaptation
    PSMSL_ADAPT_MODE_CALIBRATE,     // Initial calibration
    PSMSL_ADAPT_MODE_ADAPTIVE,      // Continuous adaptation
    PSMSL_ADAPT_MODE_HOLD,          // Hold current parameters
} psmsl_adapt_mode_t;

/**
 * @brief Adaptation speed (preserved from original)
 */
typedef enum {
    PSMSL_ADAPT_SPEED_SLOW,         // Gradual changes
    PSMSL_ADAPT_SPEED_MEDIUM,       // Balanced
    PSMSL_ADAPT_SPEED_FAST,         // Quick response
} psmsl_adapt_speed_t;

/**
 * @brief Leibniz-Bocker optimization targets
 * 
 * These replace FFT energy targets for optimization.
 */
typedef struct {
    // Coherence targets (maximize)
    float target_coherence;         // Target global coherence (0-1)
    float coherence_weight;         // Weight in optimization
    
    // Curvature targets (minimize)
    float max_curvature;            // Maximum acceptable curvature
    float curvature_weight;         // Weight in optimization
    
    // Residual targets (minimize)
    float max_residual;             // Maximum acceptable residual
    float residual_weight;          // Weight in optimization
    
    // Sector-specific targets
    float sector_coherence_target[PSMSL_NUM_SECTORS];
    float sector_energy_target[PSMSL_NUM_SECTORS];
    
    // Stability targets
    float stability_threshold;      // Minimum stability for convergence
    float novelty_threshold;        // Maximum novelty for convergence
} psmsl_lb_targets_t;

/**
 * @brief Crossover adaptation parameters (preserved structure)
 */
typedef struct {
    bool adapt_crossover_freq;
    float crossover_freq_min;
    float crossover_freq_max;
    float crossover_freq_target;
    
    bool adapt_sub_delay;
    float sub_delay_max_ms;
    bool adapt_sub_phase;
    bool adapt_sub_level;
    float sub_level_range_db;
    
    bool adapt_main_delay;
    float main_delay_max_ms;
} psmsl_crossover_params_t;

/**
 * @brief Room correction parameters (PSMSL version)
 */
typedef struct {
    // PEQ correction
    bool enable_peq;
    uint8_t max_peq_bands;
    float max_cut_db;
    float max_boost_db;
    float min_q;
    float max_q;
    
    // Sector-based targets (replaces target curve)
    bool use_sector_targets;
    float sector_target_db[PSMSL_NUM_SECTORS];
    
    // Coherence-based correction
    bool coherence_weighted;        // Weight correction by coherence
    float coherence_threshold;      // Only correct above this coherence
    
    // Frequency limits
    float correction_min_freq;
    float correction_max_freq;
} psmsl_correction_params_t;

/**
 * @brief Leibniz-Bocker optimization state
 */
typedef struct {
    // Current diagnostics
    float coherence;                // ρ: Current global coherence
    float curvature;                // Ω: Current curvature
    float residual;                 // r: Current residual
    float stability;                // Derived stability
    float novelty;                  // Derived novelty
    
    // Sector diagnostics
    float sector_coherence[PSMSL_NUM_SECTORS];
    float sector_energy[PSMSL_NUM_SECTORS];
    
    // Optimization metrics
    float cost_function;            // Combined cost (lower is better)
    float gradient_magnitude;       // Rate of improvement
    float convergence_rate;         // How fast we're converging
    
    // Grassmann manifold state
    float manifold_distance;        // Distance from target subspace
    float manifold_velocity;        // Rate of change on manifold
} psmsl_lb_state_t;

/**
 * @brief Current adaptation state (PSMSL version)
 */
typedef struct {
    // Mode
    psmsl_adapt_mode_t mode;
    psmsl_adapt_speed_t speed;
    
    // Crossover state
    float current_crossover_freq;
    float current_sub_delay_ms;
    float current_sub_phase_deg;
    float current_sub_level_db;
    float current_main_delay_ms;
    
    // PEQ state
    uint8_t active_peq_bands;
    struct {
        float freq;
        float gain_db;
        float q;
        bool active;
        uint8_t target_sector;      // Which sector this band targets
    } peq_bands[PSMSL_ADAPT_MAX_PEQ_BANDS];
    
    // Leibniz-Bocker optimization state
    psmsl_lb_state_t lb_state;
    
    // Quality metrics (derived from LB diagnostics)
    float bass_evenness;            // From sector coherence
    float integration_quality;      // From cross-sector coherence
    float overall_correction;       // Total correction applied
    
    // Convergence
    float convergence;              // 0-1, how close to optimal
    bool converged;                 // True if stable
    uint32_t iterations;            // Update count
    
    // Timestamp
    uint32_t timestamp_ms;
    uint32_t frame_count;
} psmsl_adapt_state_t;

/**
 * @brief PSMSL adaptation controller instance
 */
typedef struct {
    // Configuration
    psmsl_crossover_params_t crossover_params;
    psmsl_correction_params_t correction_params;
    psmsl_lb_targets_t lb_targets;
    
    // Current state
    psmsl_adapt_state_t state;
    
    // History for smoothing and gradient computation
    float coherence_history[PSMSL_ADAPT_HISTORY_SIZE];
    float curvature_history[PSMSL_ADAPT_HISTORY_SIZE];
    float residual_history[PSMSL_ADAPT_HISTORY_SIZE];
    float crossover_freq_history[PSMSL_ADAPT_HISTORY_SIZE];
    float sub_delay_history[PSMSL_ADAPT_HISTORY_SIZE];
    uint8_t history_index;
    uint32_t history_count;
    
    // Grassmann manifold tracking
    float target_subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    float current_subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    bool has_target_subspace;
    
    // References to other components
    audio_pipeline_t *pipeline;
    spatial_psmsl_analyzer_t *spatial;
    psmsl_mode_detector_t *mode_detector;
    
    // Timing
    uint32_t last_update_ms;
    uint32_t update_interval_ms;
    
    // State
    bool initialized;
    bool running;
} psmsl_adaptation_controller_t;

// =============================================================================
// Initialization Functions
// =============================================================================

/**
 * @brief Initialize PSMSL adaptation controller
 * 
 * @param controller    Controller instance
 * @param pipeline      Audio pipeline reference
 * @param spatial       PSMSL spatial analyzer reference
 * @param mode_detector PSMSL mode detector reference
 * @return              true on success
 */
bool psmsl_adapt_init(psmsl_adaptation_controller_t *controller,
                      audio_pipeline_t *pipeline,
                      spatial_psmsl_analyzer_t *spatial,
                      psmsl_mode_detector_t *mode_detector);

/**
 * @brief Reset controller to defaults
 * 
 * @param controller    Controller instance
 */
void psmsl_adapt_reset(psmsl_adaptation_controller_t *controller);

/**
 * @brief Set Leibniz-Bocker optimization targets
 * 
 * @param controller    Controller instance
 * @param targets       LB optimization targets
 */
void psmsl_adapt_set_lb_targets(psmsl_adaptation_controller_t *controller,
                                 const psmsl_lb_targets_t *targets);

/**
 * @brief Set crossover adaptation parameters
 * 
 * @param controller    Controller instance
 * @param params        Crossover parameters
 */
void psmsl_adapt_set_crossover_params(psmsl_adaptation_controller_t *controller,
                                       const psmsl_crossover_params_t *params);

/**
 * @brief Set room correction parameters
 * 
 * @param controller    Controller instance
 * @param params        Correction parameters
 */
void psmsl_adapt_set_correction_params(psmsl_adaptation_controller_t *controller,
                                        const psmsl_correction_params_t *params);

// =============================================================================
// Control Functions
// =============================================================================

/**
 * @brief Set adaptation mode
 * 
 * @param controller    Controller instance
 * @param mode          New mode
 */
void psmsl_adapt_set_mode(psmsl_adaptation_controller_t *controller, 
                          psmsl_adapt_mode_t mode);

/**
 * @brief Set adaptation speed
 * 
 * @param controller    Controller instance
 * @param speed         New speed
 */
void psmsl_adapt_set_speed(psmsl_adaptation_controller_t *controller, 
                           psmsl_adapt_speed_t speed);

/**
 * @brief Start calibration sequence
 * 
 * @param controller    Controller instance
 * @return              true if started
 */
bool psmsl_adapt_start_calibration(psmsl_adaptation_controller_t *controller);

/**
 * @brief Start adaptive mode
 * 
 * @param controller    Controller instance
 * @return              true if started
 */
bool psmsl_adapt_start_adaptive(psmsl_adaptation_controller_t *controller);

/**
 * @brief Stop adaptation
 * 
 * @param controller    Controller instance
 */
void psmsl_adapt_stop(psmsl_adaptation_controller_t *controller);

// =============================================================================
// Processing Functions
// =============================================================================

/**
 * @brief Main adaptation update function
 * 
 * Uses Leibniz-Bocker diagnostics to optimize parameters.
 * 
 * @param controller    Controller instance
 * @return              true if parameters were updated
 */
bool psmsl_adapt_update(psmsl_adaptation_controller_t *controller);

/**
 * @brief Process new PSMSL spatial analysis result
 * 
 * @param controller    Controller instance
 * @param spatial       New PSMSL spatial result
 */
void psmsl_adapt_process_spatial(psmsl_adaptation_controller_t *controller,
                                  const spatial_psmsl_result_t *spatial);

/**
 * @brief Process new PSMSL mode detection result
 * 
 * @param controller    Controller instance
 * @param modes         New PSMSL mode detection result
 */
void psmsl_adapt_process_modes(psmsl_adaptation_controller_t *controller,
                                const psmsl_mode_detector_result_t *modes);

// =============================================================================
// Leibniz-Bocker Optimization Functions
// =============================================================================

/**
 * @brief Compute cost function from LB diagnostics
 * 
 * Cost = w_c * (1 - coherence) + w_k * curvature + w_r * residual
 * 
 * @param controller    Controller instance
 * @return              Cost value (lower is better)
 */
float psmsl_adapt_compute_cost(const psmsl_adaptation_controller_t *controller);

/**
 * @brief Compute gradient of cost function
 * 
 * Uses history to estimate gradient direction for optimization.
 * 
 * @param controller    Controller instance
 * @param gradient      Output gradient vector [3] (coherence, curvature, residual)
 */
void psmsl_adapt_compute_gradient(const psmsl_adaptation_controller_t *controller,
                                   float gradient[3]);

/**
 * @brief Take optimization step
 * 
 * Updates parameters in direction of gradient descent.
 * 
 * @param controller    Controller instance
 * @param step_size     Step size (learning rate)
 * @return              true if step taken
 */
bool psmsl_adapt_optimization_step(psmsl_adaptation_controller_t *controller,
                                    float step_size);

/**
 * @brief Check convergence criteria
 * 
 * Converged when:
 * - Coherence > target
 * - Curvature < threshold
 * - Residual < threshold
 * - Gradient magnitude < epsilon
 * 
 * @param controller    Controller instance
 * @return              true if converged
 */
bool psmsl_adapt_check_convergence(const psmsl_adaptation_controller_t *controller);

// =============================================================================
// State Query Functions
// =============================================================================

/**
 * @brief Get current adaptation state
 * 
 * @param controller    Controller instance
 * @return              Pointer to current state
 */
const psmsl_adapt_state_t* psmsl_adapt_get_state(
    const psmsl_adaptation_controller_t *controller);

/**
 * @brief Get current LB optimization state
 * 
 * @param controller    Controller instance
 * @return              Pointer to LB state
 */
const psmsl_lb_state_t* psmsl_adapt_get_lb_state(
    const psmsl_adaptation_controller_t *controller);

/**
 * @brief Get current coherence
 * 
 * @param controller    Controller instance
 * @return              Current coherence (0-1)
 */
float psmsl_adapt_get_coherence(const psmsl_adaptation_controller_t *controller);

/**
 * @brief Get current curvature
 * 
 * @param controller    Controller instance
 * @return              Current curvature (rad/frame)
 */
float psmsl_adapt_get_curvature(const psmsl_adaptation_controller_t *controller);

/**
 * @brief Get current residual
 * 
 * @param controller    Controller instance
 * @return              Current residual (0-1)
 */
float psmsl_adapt_get_residual(const psmsl_adaptation_controller_t *controller);

/**
 * @brief Check if converged
 * 
 * @param controller    Controller instance
 * @return              true if parameters have stabilized
 */
bool psmsl_adapt_is_converged(const psmsl_adaptation_controller_t *controller);

/**
 * @brief Get convergence progress
 * 
 * @param controller    Controller instance
 * @return              Convergence (0-1)
 */
float psmsl_adapt_get_convergence(const psmsl_adaptation_controller_t *controller);

// =============================================================================
// Manual Override Functions (preserved from original)
// =============================================================================

void psmsl_adapt_set_crossover_freq(psmsl_adaptation_controller_t *controller, 
                                     float freq);
void psmsl_adapt_set_sub_delay(psmsl_adaptation_controller_t *controller, 
                                float delay_ms);
void psmsl_adapt_set_sub_level(psmsl_adaptation_controller_t *controller, 
                                float level_db);
void psmsl_adapt_set_peq_band(psmsl_adaptation_controller_t *controller,
                               uint8_t band, float freq, float gain_db, 
                               float q, bool active);

// =============================================================================
// Preset Functions (preserved from original)
// =============================================================================

bool psmsl_adapt_save_preset(psmsl_adaptation_controller_t *controller, 
                              const char *name);
bool psmsl_adapt_load_preset(psmsl_adaptation_controller_t *controller, 
                              const char *name);
int psmsl_adapt_export_json(const psmsl_adaptation_controller_t *controller,
                             char *buffer, size_t buffer_size);
bool psmsl_adapt_import_json(psmsl_adaptation_controller_t *controller, 
                              const char *json);

// =============================================================================
// Compatibility Layer
// =============================================================================

#ifdef USE_PSMSL_ANALYSIS

// Redirect old adaptation functions to PSMSL versions
#define adaptation_controller_t     psmsl_adaptation_controller_t
#define adapt_state_t               psmsl_adapt_state_t
#define adapt_mode_t                psmsl_adapt_mode_t
#define adapt_speed_t               psmsl_adapt_speed_t
#define adapt_init                  psmsl_adapt_init
#define adapt_reset                 psmsl_adapt_reset
#define adapt_update                psmsl_adapt_update
#define adapt_get_state             psmsl_adapt_get_state

#endif // USE_PSMSL_ANALYSIS

#ifdef __cplusplus
}
#endif

#endif // ADAPTATION_CONTROLLER_PSMSL_H
