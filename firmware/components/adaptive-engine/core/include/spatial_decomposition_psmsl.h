/**
 * @file spatial_decomposition_psmsl.h
 * @brief PSMSL-based spatial mode decomposition
 * 
 * Replaces FFT-based 4-mode decomposition with PSMSL 7 semantic sectors.
 * Uses covariance geometry and Grassmann manifold tracking instead of
 * traditional spectral analysis.
 * 
 * Theoretical Foundation:
 * - Leibniz-Bocker Framework: Covariance geometry as primary analysis
 * - Thyme Identity: π² = (7φ² + √2) / 2 defines 7 semantic sectors
 * - Grassmann Manifold: Eigenspace trajectories for structural tracking
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef SPATIAL_DECOMPOSITION_PSMSL_H
#define SPATIAL_DECOMPOSITION_PSMSL_H

#include <stdint.h>
#include <stdbool.h>
#include "pdm_mic_driver.h"
#include "psmsl_analysis.h"
#include "psmsl_grassmann.h"

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

// Use PSMSL 7 semantic sectors instead of 4 FFT modes
#define SPATIAL_PSMSL_NUM_SECTORS   PSMSL_NUM_SECTORS   // 7 sectors
#define SPATIAL_PSMSL_HISTORY_SIZE  16                   // Temporal averaging

// =============================================================================
// Types
// =============================================================================

/**
 * @brief PSMSL-based spatial sector type
 * 
 * Maps to the 7 semantic sectors from the Thyme Identity.
 */
typedef enum {
    SPATIAL_SECTOR_FOUNDATION = 0,  // 20-80 Hz: Sub-bass, room modes
    SPATIAL_SECTOR_STRUCTURE,       // 80-200 Hz: Bass fundamentals
    SPATIAL_SECTOR_BODY,            // 200-500 Hz: Warmth, body
    SPATIAL_SECTOR_PRESENCE,        // 500-2000 Hz: Vocals, instruments
    SPATIAL_SECTOR_CLARITY,         // 2000-5000 Hz: Articulation
    SPATIAL_SECTOR_AIR,             // 5000-10000 Hz: Brightness
    SPATIAL_SECTOR_EXTENSION,       // 10000-20000 Hz: Ultra-high
} spatial_sector_type_t;

/**
 * @brief PSMSL spatial analysis result per sector
 */
typedef struct {
    float center_freq;              // Sector center frequency (Hz)
    float energy_linear;            // Linear energy
    float energy_db;                // Energy in dB
    float coherence;                // Sector coherence (0-1)
    float phase;                    // Dominant phase (radians)
    float phi_weight;               // φ-scaled weight
    float eigenvalue_ratio;         // Contribution to total eigenvalue sum
} spatial_sector_result_t;

/**
 * @brief Direction of arrival estimate (preserved from original)
 */
typedef struct {
    float azimuth;                  // Horizontal angle (degrees, 0 = front)
    float elevation;                // Vertical angle (degrees, 0 = horizontal)
    float confidence;               // Confidence level (0-1)
    float spread;                   // Angular spread (degrees)
} spatial_doa_estimate_t;

/**
 * @brief Complete PSMSL spatial analysis result
 */
typedef struct {
    // Per-sector results (7 semantic sectors)
    spatial_sector_result_t sectors[SPATIAL_PSMSL_NUM_SECTORS];
    
    // Leibniz-Bocker diagnostics (replace FFT metrics)
    float coherence;                // ρ: Global coherence (0-1)
    float curvature;                // Ω: Structural change rate (rad/frame)
    float residual;                 // r: Unexplained variance (0-1)
    
    // Derived diagnostics
    float stability;                // 1 / (1 + curvature)
    float novelty;                  // residual * (1 - coherence)
    
    // Summary metrics
    float total_energy_db;          // Total energy across all sectors
    float spectral_centroid;        // Energy-weighted center frequency
    float spectral_spread;          // Standard deviation of spectrum
    float diffuseness;              // Sound field diffuseness (0-1)
    
    // Direction of arrival
    spatial_doa_estimate_t doa;
    
    // Grassmann manifold state
    float grassmann_distance;       // Distance from previous frame
    float principal_angle_max;      // Maximum principal angle
    
    // Timestamp
    uint32_t timestamp_ms;
    uint32_t frame_count;
    
    // Validity
    bool valid;
} spatial_psmsl_result_t;

/**
 * @brief PSMSL spatial decomposition analyzer
 */
typedef struct {
    // Configuration
    float sample_rate;
    uint8_t num_mics;
    mic_array_geometry_t geometry;
    
    // PSMSL analyzer (replaces FFT)
    psmsl_analyzer_t psmsl;
    
    // Grassmann manifold tracking
    float subspace_prev[GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    float subspace_curr[GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    bool has_previous_subspace;
    
    // Sector projection matrix (mic geometry to sectors)
    float sector_weights[SPATIAL_PSMSL_NUM_SECTORS][MIC_ARRAY_CHANNELS];
    
    // Results
    spatial_psmsl_result_t result;
    spatial_psmsl_result_t history[SPATIAL_PSMSL_HISTORY_SIZE];
    uint8_t history_index;
    
    // State
    bool initialized;
    bool calibrated;
} spatial_psmsl_analyzer_t;

// =============================================================================
// Initialization Functions
// =============================================================================

/**
 * @brief Initialize PSMSL spatial analyzer
 * 
 * @param analyzer      Analyzer instance
 * @param sample_rate   Sample rate (Hz)
 * @param geometry      Microphone array geometry
 * @return              true on success
 */
bool spatial_psmsl_init(spatial_psmsl_analyzer_t *analyzer,
                        float sample_rate,
                        const mic_array_geometry_t *geometry);

/**
 * @brief Reset analyzer state
 * 
 * @param analyzer      Analyzer instance
 */
void spatial_psmsl_reset(spatial_psmsl_analyzer_t *analyzer);

/**
 * @brief Update microphone geometry
 * 
 * Recalculates sector projection weights.
 * 
 * @param analyzer      Analyzer instance
 * @param geometry      New geometry
 */
void spatial_psmsl_set_geometry(spatial_psmsl_analyzer_t *analyzer,
                                const mic_array_geometry_t *geometry);

/**
 * @brief Calibrate analyzer with reference signal
 * 
 * @param analyzer      Analyzer instance
 * @param ref_data      Reference signal data from all mics
 * @param frames        Number of frames
 * @return              true on success
 */
bool spatial_psmsl_calibrate(spatial_psmsl_analyzer_t *analyzer,
                             const float *const *ref_data,
                             uint32_t frames);

// =============================================================================
// Analysis Functions
// =============================================================================

/**
 * @brief Feed microphone data to analyzer
 * 
 * @param analyzer      Analyzer instance
 * @param mic_data      Array of mic channel buffers [channel][sample]
 * @param frames        Number of frames
 * @return              true if new result available
 */
bool spatial_psmsl_feed(spatial_psmsl_analyzer_t *analyzer,
                        const float *const *mic_data,
                        uint32_t frames);

/**
 * @brief Process and compute PSMSL spatial decomposition
 * 
 * @param analyzer      Analyzer instance
 * @return              true on success
 */
bool spatial_psmsl_process(spatial_psmsl_analyzer_t *analyzer);

/**
 * @brief Get latest spatial analysis result
 * 
 * @param analyzer      Analyzer instance
 * @return              Pointer to result (valid until next process)
 */
const spatial_psmsl_result_t* spatial_psmsl_get_result(const spatial_psmsl_analyzer_t *analyzer);

// =============================================================================
// Sector Access Functions
// =============================================================================

/**
 * @brief Get sector energy
 * 
 * @param analyzer      Analyzer instance
 * @param sector        Sector index (0-6)
 * @return              Energy in dB
 */
float spatial_psmsl_get_sector_energy(const spatial_psmsl_analyzer_t *analyzer, 
                                       uint8_t sector);

/**
 * @brief Get sector coherence
 * 
 * @param analyzer      Analyzer instance
 * @param sector        Sector index (0-6)
 * @return              Coherence (0-1)
 */
float spatial_psmsl_get_sector_coherence(const spatial_psmsl_analyzer_t *analyzer,
                                          uint8_t sector);

/**
 * @brief Get sector φ-weight
 * 
 * @param analyzer      Analyzer instance
 * @param sector        Sector index (0-6)
 * @return              φ-scaled weight
 */
float spatial_psmsl_get_sector_phi_weight(const spatial_psmsl_analyzer_t *analyzer,
                                           uint8_t sector);

// =============================================================================
// Leibniz-Bocker Diagnostic Accessors
// =============================================================================

/**
 * @brief Get global coherence (ρ)
 * 
 * Measures effective dimensionality of the spatial sound field.
 * 
 * @param analyzer      Analyzer instance
 * @return              Coherence (0-1)
 */
float spatial_psmsl_get_coherence(const spatial_psmsl_analyzer_t *analyzer);

/**
 * @brief Get curvature (Ω)
 * 
 * Measures rate of structural change on Grassmann manifold.
 * 
 * @param analyzer      Analyzer instance
 * @return              Curvature (rad/frame)
 */
float spatial_psmsl_get_curvature(const spatial_psmsl_analyzer_t *analyzer);

/**
 * @brief Get residual (r)
 * 
 * Measures unexplained variance / novelty in the signal.
 * 
 * @param analyzer      Analyzer instance
 * @return              Residual (0-1)
 */
float spatial_psmsl_get_residual(const spatial_psmsl_analyzer_t *analyzer);

/**
 * @brief Get stability
 * 
 * Derived from curvature: 1 / (1 + curvature)
 * 
 * @param analyzer      Analyzer instance
 * @return              Stability (0-1)
 */
float spatial_psmsl_get_stability(const spatial_psmsl_analyzer_t *analyzer);

/**
 * @brief Get novelty
 * 
 * Derived: residual * (1 - coherence)
 * 
 * @param analyzer      Analyzer instance
 * @return              Novelty (0-1)
 */
float spatial_psmsl_get_novelty(const spatial_psmsl_analyzer_t *analyzer);

// =============================================================================
// Direction of Arrival Functions
// =============================================================================

/**
 * @brief Estimate direction of arrival using PSMSL
 * 
 * Uses sector coherence patterns to estimate DOA.
 * 
 * @param analyzer      Analyzer instance
 * @param doa           Output DOA estimate
 * @return              true if valid estimate
 */
bool spatial_psmsl_estimate_doa(const spatial_psmsl_analyzer_t *analyzer,
                                 spatial_doa_estimate_t *doa);

/**
 * @brief Get broadband DOA estimate
 * 
 * @param analyzer      Analyzer instance
 * @return              Pointer to DOA estimate
 */
const spatial_doa_estimate_t* spatial_psmsl_get_doa(const spatial_psmsl_analyzer_t *analyzer);

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * @brief Get sector center frequency
 * 
 * @param sector        Sector index (0-6)
 * @return              Center frequency in Hz
 */
float spatial_psmsl_sector_to_freq(uint8_t sector);

/**
 * @brief Get sector index for frequency
 * 
 * @param freq          Frequency in Hz
 * @return              Sector index (0-6)
 */
uint8_t spatial_psmsl_freq_to_sector(float freq);

/**
 * @brief Get sector name string
 * 
 * @param sector        Sector index (0-6)
 * @return              Human-readable sector name
 */
const char* spatial_psmsl_sector_name(uint8_t sector);

/**
 * @brief Calculate diffuseness from PSMSL analysis
 * 
 * @param analyzer      Analyzer instance
 * @return              Diffuseness (0 = directional, 1 = diffuse)
 */
float spatial_psmsl_calculate_diffuseness(const spatial_psmsl_analyzer_t *analyzer);

// =============================================================================
// Compatibility Layer
// =============================================================================

#ifdef USE_PSMSL_ANALYSIS

// Redirect old spatial functions to PSMSL versions
#define spatial_analyzer_t          spatial_psmsl_analyzer_t
#define spatial_result_t            spatial_psmsl_result_t
#define spatial_init                spatial_psmsl_init
#define spatial_reset               spatial_psmsl_reset
#define spatial_feed                spatial_psmsl_feed
#define spatial_process             spatial_psmsl_process
#define spatial_get_result          spatial_psmsl_get_result

#endif // USE_PSMSL_ANALYSIS

#ifdef __cplusplus
}
#endif

#endif // SPATIAL_DECOMPOSITION_PSMSL_H
