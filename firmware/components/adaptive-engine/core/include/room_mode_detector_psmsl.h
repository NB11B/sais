/**
 * @file room_mode_detector_psmsl.h
 * @brief PSMSL-based room acoustic mode detection
 * 
 * Replaces FFT peak detection with Leibniz-Bocker diagnostics
 * (Coherence, Curvature, Residual) for room mode analysis.
 * 
 * Key differences from FFT-based detection:
 * - Uses Coherence (ρ) to identify structured resonances
 * - Uses Curvature (Ω) to detect mode transitions
 * - Uses Residual (r) to identify novel acoustic events
 * - Tracks modes on Grassmann manifold for temporal consistency
 * 
 * Theoretical Foundation:
 * - Leibniz-Bocker Framework: Covariance geometry for mode detection
 * - Grassmann Manifold: Eigenspace trajectories for mode tracking
 * - Thyme Identity: 7 semantic sectors for frequency organization
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef ROOM_MODE_DETECTOR_PSMSL_H
#define ROOM_MODE_DETECTOR_PSMSL_H

#include <stdint.h>
#include <stdbool.h>
#include "spatial_decomposition_psmsl.h"
#include "psmsl_analysis.h"

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

#define PSMSL_MAX_ROOM_MODES    16      // Maximum modes to track
#define PSMSL_MODE_HISTORY      32      // Temporal history for mode tracking

// =============================================================================
// Types
// =============================================================================

/**
 * @brief Room mode type classification (preserved from original)
 */
typedef enum {
    PSMSL_MODE_TYPE_UNKNOWN,
    PSMSL_MODE_TYPE_AXIAL,      // Single axis (L, W, or H)
    PSMSL_MODE_TYPE_TANGENTIAL, // Two axes
    PSMSL_MODE_TYPE_OBLIQUE,    // Three axes
} psmsl_room_mode_type_t;

/**
 * @brief Leibniz-Bocker mode detection state
 * 
 * Each mode has its own diagnostic trajectory.
 */
typedef struct {
    float coherence;            // ρ: Mode coherence (0-1)
    float curvature;            // Ω: Mode stability (rad/frame)
    float residual;             // r: Mode novelty (0-1)
    float stability;            // Derived: 1 / (1 + curvature)
    float trajectory_length;    // Accumulated Grassmann distance
} lb_mode_state_t;

/**
 * @brief Detected room mode (PSMSL version)
 */
typedef struct {
    // Frequency characteristics
    float frequency;            // Mode frequency (Hz)
    float bandwidth;            // Mode bandwidth (Hz)
    float q_factor;             // Q factor (frequency/bandwidth)
    float magnitude_db;         // Mode magnitude (dB)
    float decay_time_ms;        // RT60-like decay time
    psmsl_room_mode_type_t type;// Mode classification
    
    // Semantic sector mapping
    uint8_t primary_sector;     // Primary semantic sector (0-6)
    float sector_energy[PSMSL_NUM_SECTORS]; // Energy distribution
    
    // Leibniz-Bocker diagnostics for this mode
    lb_mode_state_t lb_state;
    
    // Spatial characteristics
    float spatial_coherence;    // Coherence across mic array
    uint8_t nodal_positions;    // Bitmask of mics at nodes
    
    // Correction suggestion
    float suggested_eq_freq;    // Suggested PEQ center frequency
    float suggested_eq_gain;    // Suggested PEQ gain (negative = cut)
    float suggested_eq_q;       // Suggested PEQ Q factor
    
    // Tracking
    bool active;                // Mode currently active
    uint32_t persistence;       // Frames mode has been detected
    float confidence;           // Detection confidence (0-1)
    float grassmann_distance;   // Distance on manifold from last frame
} psmsl_room_mode_t;

/**
 * @brief Room dimensions estimate (preserved)
 */
typedef struct {
    float length;               // Estimated length (m)
    float width;                // Estimated width (m)
    float height;               // Estimated height (m)
    float confidence;           // Estimate confidence (0-1)
} psmsl_room_dimensions_t;

/**
 * @brief PSMSL room mode detector result
 */
typedef struct {
    // Detected modes
    psmsl_room_mode_t modes[PSMSL_MAX_ROOM_MODES];
    uint8_t num_modes;
    
    // Global Leibniz-Bocker diagnostics
    float global_coherence;     // ρ: Overall field coherence
    float global_curvature;     // Ω: Overall structural change
    float global_residual;      // r: Overall novelty
    
    // Room characteristics
    psmsl_room_dimensions_t dimensions;
    float rt60_estimate;        // Estimated RT60 (seconds)
    float modal_density;        // Modes per Hz in low frequency
    float schroeder_freq;       // Schroeder frequency (Hz)
    
    // Per-sector analysis
    float sector_mode_count[PSMSL_NUM_SECTORS];     // Modes per sector
    float sector_energy[PSMSL_NUM_SECTORS];         // Energy per sector
    float sector_coherence[PSMSL_NUM_SECTORS];      // Coherence per sector
    
    // Overall quality metrics
    float bass_evenness;        // Evenness of bass response (0-1)
    float modal_ringing;        // Amount of modal ringing (0-1)
    float correction_urgency;   // How much correction is needed (0-1)
    
    // Grassmann manifold state
    float manifold_velocity;    // Rate of change on manifold
    float manifold_curvature;   // Curvature of trajectory
    
    // Timestamp
    uint32_t timestamp_ms;
    uint32_t frame_count;
    
    // Validity
    bool valid;
} psmsl_mode_detector_result_t;

/**
 * @brief PSMSL room mode detector instance
 */
typedef struct {
    // Configuration
    float sample_rate;
    float speed_of_sound;       // m/s (default 343)
    
    // Detection thresholds (Leibniz-Bocker based)
    float coherence_threshold;  // Minimum coherence to detect mode
    float curvature_threshold;  // Maximum curvature for stable mode
    float residual_threshold;   // Maximum residual for known mode
    
    // Sector-based history for temporal analysis
    float sector_history[PSMSL_MODE_HISTORY][PSMSL_NUM_SECTORS];
    float coherence_history[PSMSL_MODE_HISTORY];
    float curvature_history[PSMSL_MODE_HISTORY];
    uint8_t history_index;
    uint32_t history_count;
    
    // Grassmann manifold tracking for mode evolution
    float subspace_history[PSMSL_MODE_HISTORY][GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    
    // Results
    psmsl_mode_detector_result_t result;
    
    // State
    bool initialized;
    bool dimensions_known;
} psmsl_mode_detector_t;

// =============================================================================
// Initialization Functions
// =============================================================================

/**
 * @brief Initialize PSMSL room mode detector
 * 
 * @param detector      Detector instance
 * @param sample_rate   Sample rate (Hz)
 * @return              true on success
 */
bool psmsl_mode_detector_init(psmsl_mode_detector_t *detector, float sample_rate);

/**
 * @brief Reset detector state
 * 
 * @param detector      Detector instance
 */
void psmsl_mode_detector_reset(psmsl_mode_detector_t *detector);

/**
 * @brief Set known room dimensions
 * 
 * @param detector      Detector instance
 * @param length        Room length (m)
 * @param width         Room width (m)
 * @param height        Room height (m)
 */
void psmsl_mode_detector_set_dimensions(psmsl_mode_detector_t *detector,
                                         float length, float width, float height);

/**
 * @brief Set Leibniz-Bocker detection thresholds
 * 
 * @param detector              Detector instance
 * @param coherence_threshold   Minimum coherence for mode detection
 * @param curvature_threshold   Maximum curvature for stable mode
 * @param residual_threshold    Maximum residual for known mode
 */
void psmsl_mode_detector_set_thresholds(psmsl_mode_detector_t *detector,
                                         float coherence_threshold,
                                         float curvature_threshold,
                                         float residual_threshold);

// =============================================================================
// Detection Functions
// =============================================================================

/**
 * @brief Process PSMSL spatial analysis result
 * 
 * Uses Leibniz-Bocker diagnostics for mode detection.
 * 
 * @param detector      Detector instance
 * @param spatial       PSMSL spatial analysis result
 * @return              true if modes detected/updated
 */
bool psmsl_mode_detector_process(psmsl_mode_detector_t *detector,
                                  const spatial_psmsl_result_t *spatial);

/**
 * @brief Process PSMSL analysis result directly
 * 
 * @param detector      Detector instance
 * @param psmsl         PSMSL analysis result
 * @return              true if modes detected/updated
 */
bool psmsl_mode_detector_process_psmsl(psmsl_mode_detector_t *detector,
                                        const psmsl_result_t *psmsl);

/**
 * @brief Get detection result
 * 
 * @param detector      Detector instance
 * @return              Pointer to result
 */
const psmsl_mode_detector_result_t* psmsl_mode_detector_get_result(
    const psmsl_mode_detector_t *detector);

// =============================================================================
// Mode Query Functions
// =============================================================================

/**
 * @brief Get number of detected modes
 * 
 * @param detector      Detector instance
 * @return              Number of active modes
 */
uint8_t psmsl_mode_detector_get_mode_count(const psmsl_mode_detector_t *detector);

/**
 * @brief Get mode by index
 * 
 * @param detector      Detector instance
 * @param index         Mode index
 * @return              Pointer to mode (NULL if invalid)
 */
const psmsl_room_mode_t* psmsl_mode_detector_get_mode(
    const psmsl_mode_detector_t *detector, uint8_t index);

/**
 * @brief Find mode in semantic sector
 * 
 * @param detector      Detector instance
 * @param sector        Sector index (0-6)
 * @return              Pointer to mode (NULL if none)
 */
const psmsl_room_mode_t* psmsl_mode_detector_find_mode_in_sector(
    const psmsl_mode_detector_t *detector, uint8_t sector);

/**
 * @brief Get most problematic mode (highest coherence, low stability)
 * 
 * @param detector      Detector instance
 * @return              Pointer to mode (NULL if none)
 */
const psmsl_room_mode_t* psmsl_mode_detector_get_worst_mode(
    const psmsl_mode_detector_t *detector);

/**
 * @brief Get most stable mode (high coherence, low curvature)
 * 
 * @param detector      Detector instance
 * @return              Pointer to mode (NULL if none)
 */
const psmsl_room_mode_t* psmsl_mode_detector_get_most_stable_mode(
    const psmsl_mode_detector_t *detector);

// =============================================================================
// Leibniz-Bocker Diagnostic Queries
// =============================================================================

/**
 * @brief Get global coherence
 * 
 * @param detector      Detector instance
 * @return              Global coherence (0-1)
 */
float psmsl_mode_detector_get_coherence(const psmsl_mode_detector_t *detector);

/**
 * @brief Get global curvature
 * 
 * @param detector      Detector instance
 * @return              Global curvature (rad/frame)
 */
float psmsl_mode_detector_get_curvature(const psmsl_mode_detector_t *detector);

/**
 * @brief Get global residual
 * 
 * @param detector      Detector instance
 * @return              Global residual (0-1)
 */
float psmsl_mode_detector_get_residual(const psmsl_mode_detector_t *detector);

/**
 * @brief Get sector coherence
 * 
 * @param detector      Detector instance
 * @param sector        Sector index (0-6)
 * @return              Sector coherence (0-1)
 */
float psmsl_mode_detector_get_sector_coherence(
    const psmsl_mode_detector_t *detector, uint8_t sector);

// =============================================================================
// Correction Suggestion Functions
// =============================================================================

/**
 * @brief Generate PEQ correction for a mode
 * 
 * Uses Leibniz-Bocker diagnostics to determine correction parameters.
 * 
 * @param mode          Mode to correct
 * @param freq          Output: PEQ center frequency
 * @param gain_db       Output: PEQ gain (negative = cut)
 * @param q             Output: PEQ Q factor
 */
void psmsl_mode_detector_suggest_peq(const psmsl_room_mode_t *mode,
                                      float *freq, float *gain_db, float *q);

/**
 * @brief Generate sector-based correction curve
 * 
 * @param detector      Detector instance
 * @param correction_db Output: correction per sector [PSMSL_NUM_SECTORS]
 * @param max_cut_db    Maximum cut to apply (positive value)
 * @param max_boost_db  Maximum boost to apply (positive value)
 */
void psmsl_mode_detector_generate_correction(
    const psmsl_mode_detector_t *detector,
    float correction_db[PSMSL_NUM_SECTORS],
    float max_cut_db,
    float max_boost_db);

// =============================================================================
// Room Analysis Functions
// =============================================================================

/**
 * @brief Estimate room dimensions from sector analysis
 * 
 * @param detector      Detector instance
 * @param dimensions    Output: estimated dimensions
 * @return              true if estimate is valid
 */
bool psmsl_mode_detector_estimate_dimensions(
    const psmsl_mode_detector_t *detector,
    psmsl_room_dimensions_t *dimensions);

/**
 * @brief Calculate Schroeder frequency
 * 
 * @param detector      Detector instance
 * @return              Schroeder frequency (Hz)
 */
float psmsl_mode_detector_get_schroeder_freq(const psmsl_mode_detector_t *detector);

/**
 * @brief Get modal density in sector
 * 
 * @param detector      Detector instance
 * @param sector        Sector index (0-6)
 * @return              Modal density (modes per Hz)
 */
float psmsl_mode_detector_get_sector_modal_density(
    const psmsl_mode_detector_t *detector, uint8_t sector);

// =============================================================================
// Compatibility Layer
// =============================================================================

#ifdef USE_PSMSL_ANALYSIS

// Redirect old mode detector functions to PSMSL versions
#define room_mode_detector_t        psmsl_mode_detector_t
#define mode_detector_result_t      psmsl_mode_detector_result_t
#define room_mode_t                 psmsl_room_mode_t
#define mode_detector_init          psmsl_mode_detector_init
#define mode_detector_reset         psmsl_mode_detector_reset
#define mode_detector_process       psmsl_mode_detector_process
#define mode_detector_get_result    psmsl_mode_detector_get_result

#endif // USE_PSMSL_ANALYSIS

#ifdef __cplusplus
}
#endif

#endif // ROOM_MODE_DETECTOR_PSMSL_H
