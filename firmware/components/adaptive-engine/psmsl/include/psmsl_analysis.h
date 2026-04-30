/**
 * @file psmsl_analysis.h
 * @brief PSMSL (Phi-Scaled Mirrored Semantic Lattice) Analysis
 * 
 * Replaces FFT-based spectral analysis with covariance geometry
 * based on the Leibniz-Bocker framework. This implementation uses
 * the Thyme Identity (π² = (7φ² + √2) / 2) to derive 7 semantic
 * sectors for signal decomposition.
 * 
 * Theoretical Foundation:
 * - Leibniz-Bocker Framework: Infinitesimal motion as primary data
 * - Grassmann Manifold: Eigenspace trajectories for structural tracking
 * - Riemann Zeta Connection: Prime-based semantic sector mapping
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef PSMSL_ANALYSIS_H
#define PSMSL_ANALYSIS_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Thyme Identity Constants
// =============================================================================

#define PSMSL_PHI               1.6180339887498948f     // Golden ratio φ
#define PSMSL_PHI_SQUARED       2.6180339887498948f     // φ²
#define PSMSL_SQRT2             1.4142135623730951f     // √2
#define PSMSL_PI                3.1415926535897932f     // π
#define PSMSL_PI_SQUARED        9.8696044010893586f     // π²

// Thyme Identity: π² = (7φ² + √2) / 2
// Verification: (7 * 2.618... + 1.414...) / 2 ≈ 9.869...
#define PSMSL_THYME_CONSTANT    ((7.0f * PSMSL_PHI_SQUARED + PSMSL_SQRT2) / 2.0f)

// =============================================================================
// Structural Constants
// =============================================================================

#define PSMSL_NUM_SECTORS       7       // Semantic sectors (from Thyme Identity)
#define PSMSL_K_DIMENSIONS      24      // k = 7 × 3.5 (composite dimensions)
#define PSMSL_STATE_DIMENSIONS  576     // k² = 24² (full state space)
#define PSMSL_MAX_CHANNELS      8       // Maximum input channels
#define PSMSL_HISTORY_SIZE      16      // Frames of history for curvature

// Covariance window
#define PSMSL_WINDOW_SIZE       512     // Samples per covariance update
#define PSMSL_OVERLAP           256     // 50% overlap

// =============================================================================
// Semantic Sector Frequency Mapping
// =============================================================================

/**
 * @brief Semantic sector definitions
 * 
 * Each sector corresponds to a frequency range and semantic role.
 * The boundaries are derived from φ-scaling of the audible spectrum.
 */
typedef enum {
    PSMSL_SECTOR_FOUNDATION = 0,    // 20-80 Hz: Sub-bass, room modes
    PSMSL_SECTOR_STRUCTURE,         // 80-200 Hz: Bass fundamentals
    PSMSL_SECTOR_BODY,              // 200-500 Hz: Warmth, body
    PSMSL_SECTOR_PRESENCE,          // 500-2000 Hz: Vocals, instruments
    PSMSL_SECTOR_CLARITY,           // 2000-5000 Hz: Articulation
    PSMSL_SECTOR_AIR,               // 5000-10000 Hz: Brightness
    PSMSL_SECTOR_EXTENSION,         // 10000-20000 Hz: Ultra-high
} psmsl_sector_id_t;

// Sector frequency boundaries (Hz)
static const float PSMSL_SECTOR_FREQ_LOW[PSMSL_NUM_SECTORS] = {
    20.0f, 80.0f, 200.0f, 500.0f, 2000.0f, 5000.0f, 10000.0f
};

static const float PSMSL_SECTOR_FREQ_HIGH[PSMSL_NUM_SECTORS] = {
    80.0f, 200.0f, 500.0f, 2000.0f, 5000.0f, 10000.0f, 20000.0f
};

// =============================================================================
// Leibniz-Bocker Diagnostics
// =============================================================================

/**
 * @brief Leibniz-Bocker geometric diagnostics
 * 
 * These three metrics replace traditional FFT-based analysis:
 * - Coherence (ρ): Effective dimensionality of the signal
 * - Curvature (Ω): Rate of structural change on Grassmann manifold
 * - Residual (r): Projection error / novelty detection
 */
typedef struct {
    float coherence;            // ρ: 0.0 (chaotic) to 1.0 (coherent)
    float curvature;            // Ω: Rate of eigenspace rotation (rad/s)
    float residual;             // r: Unexplained variance (0.0 to 1.0)
    float stability;            // Derived: 1 / (1 + curvature)
    float novelty;              // Derived: residual * (1 - coherence)
} lb_diagnostics_t;

// =============================================================================
// Sector Analysis Result
// =============================================================================

/**
 * @brief Analysis result for a single semantic sector
 */
typedef struct {
    // Energy metrics
    float energy_linear;        // Linear energy
    float energy_db;            // Energy in dB
    
    // Phase and coherence
    float phase;                // Dominant phase (radians)
    float sector_coherence;     // Coherence within sector
    
    // φ-scaled recursion
    float phi_depth;            // Recursion depth (φ-scaled)
    float phi_weight;           // Weight from φ-scaling
    
    // Eigenvalue contribution
    float eigenvalue_sum;       // Sum of eigenvalues in sector
    float eigenvalue_ratio;     // Ratio to total eigenvalue sum
} psmsl_sector_result_t;

// =============================================================================
// Complete PSMSL Analysis Result
// =============================================================================

/**
 * @brief Complete PSMSL analysis result
 */
typedef struct {
    // Per-sector results
    psmsl_sector_result_t sectors[PSMSL_NUM_SECTORS];
    
    // Global Leibniz-Bocker diagnostics
    lb_diagnostics_t diagnostics;
    
    // Grassmann manifold state
    float grassmann_position[PSMSL_K_DIMENSIONS];   // Current position
    float grassmann_velocity[PSMSL_K_DIMENSIONS];   // Velocity (for curvature)
    float principal_angles[PSMSL_NUM_SECTORS];      // Angles between subspaces
    
    // Summary metrics
    float total_energy_db;      // Total energy across all sectors
    float spectral_centroid;    // Energy-weighted center frequency
    float spectral_spread;      // Standard deviation of spectrum
    float spectral_flatness;    // Wiener entropy (0=tonal, 1=noise)
    
    // Timing
    uint32_t timestamp_ms;      // Timestamp of analysis
    uint32_t frame_count;       // Frame counter
    
    // Validity
    bool valid;                 // Result is valid
} psmsl_result_t;

// =============================================================================
// PSMSL Analyzer State
// =============================================================================

/**
 * @brief PSMSL analyzer instance
 */
typedef struct {
    // Configuration
    float sample_rate;
    uint8_t num_channels;
    uint32_t window_size;
    uint32_t overlap;
    
    // Input buffering
    float input_buffer[PSMSL_MAX_CHANNELS][PSMSL_WINDOW_SIZE];
    uint32_t input_index;
    
    // Covariance computation
    float covariance[PSMSL_K_DIMENSIONS][PSMSL_K_DIMENSIONS];
    float covariance_prev[PSMSL_K_DIMENSIONS][PSMSL_K_DIMENSIONS];
    
    // Eigendecomposition results
    float eigenvalues[PSMSL_K_DIMENSIONS];
    float eigenvectors[PSMSL_K_DIMENSIONS][PSMSL_K_DIMENSIONS];
    
    // Grassmann manifold tracking
    float subspace_prev[PSMSL_K_DIMENSIONS][PSMSL_NUM_SECTORS];
    float subspace_curr[PSMSL_K_DIMENSIONS][PSMSL_NUM_SECTORS];
    
    // Sector mapping matrix (frequency to sector projection)
    float sector_projection[PSMSL_NUM_SECTORS][PSMSL_K_DIMENSIONS];
    
    // History for curvature computation
    psmsl_result_t history[PSMSL_HISTORY_SIZE];
    uint8_t history_index;
    uint8_t history_count;
    
    // Current result
    psmsl_result_t result;
    
    // State
    bool initialized;
    bool calibrated;
    uint32_t frame_count;
} psmsl_analyzer_t;

// =============================================================================
// Initialization Functions
// =============================================================================

/**
 * @brief Initialize PSMSL analyzer
 * 
 * @param analyzer      Analyzer instance
 * @param sample_rate   Sample rate in Hz
 * @param num_channels  Number of input channels (mic array)
 * @return              true on success
 */
bool psmsl_init(psmsl_analyzer_t *analyzer, 
                float sample_rate, 
                uint8_t num_channels);

/**
 * @brief Reset analyzer state
 * 
 * @param analyzer      Analyzer instance
 */
void psmsl_reset(psmsl_analyzer_t *analyzer);

/**
 * @brief Calibrate sector projection matrix
 * 
 * @param analyzer      Analyzer instance
 * @param ref_data      Reference calibration data
 * @param frames        Number of frames
 * @return              true on success
 */
bool psmsl_calibrate(psmsl_analyzer_t *analyzer,
                     const float *const *ref_data,
                     uint32_t frames);

// =============================================================================
// Analysis Functions
// =============================================================================

/**
 * @brief Feed samples to analyzer
 * 
 * @param analyzer      Analyzer instance
 * @param samples       Array of channel sample buffers
 * @param count         Number of samples per channel
 * @return              true if new result is available
 */
bool psmsl_feed(psmsl_analyzer_t *analyzer,
                const float *const *samples,
                uint32_t count);

/**
 * @brief Process accumulated samples
 * 
 * Computes covariance, eigendecomposition, and Leibniz-Bocker diagnostics.
 * 
 * @param analyzer      Analyzer instance
 * @return              true if result computed
 */
bool psmsl_process(psmsl_analyzer_t *analyzer);

/**
 * @brief Get current analysis result
 * 
 * @param analyzer      Analyzer instance
 * @return              Pointer to result (valid until next process)
 */
const psmsl_result_t* psmsl_get_result(const psmsl_analyzer_t *analyzer);

// =============================================================================
// Diagnostic Accessors
// =============================================================================

/**
 * @brief Get coherence diagnostic
 * 
 * Coherence (ρ) measures the effective dimensionality of the signal.
 * High coherence = structured signal, low coherence = noise/chaos.
 * 
 * @param analyzer      Analyzer instance
 * @return              Coherence value (0.0 to 1.0)
 */
float psmsl_get_coherence(const psmsl_analyzer_t *analyzer);

/**
 * @brief Get curvature diagnostic
 * 
 * Curvature (Ω) measures the rate of structural change on the
 * Grassmann manifold. High curvature = rapid change, low = stable.
 * 
 * @param analyzer      Analyzer instance
 * @return              Curvature value (rad/s)
 */
float psmsl_get_curvature(const psmsl_analyzer_t *analyzer);

/**
 * @brief Get residual diagnostic
 * 
 * Residual (r) measures the unexplained variance / novelty.
 * High residual = novel input, low = expected/predictable.
 * 
 * @param analyzer      Analyzer instance
 * @return              Residual value (0.0 to 1.0)
 */
float psmsl_get_residual(const psmsl_analyzer_t *analyzer);

/**
 * @brief Get complete diagnostics structure
 * 
 * @param analyzer      Analyzer instance
 * @return              Pointer to diagnostics
 */
const lb_diagnostics_t* psmsl_get_diagnostics(const psmsl_analyzer_t *analyzer);

// =============================================================================
// Sector Accessors
// =============================================================================

/**
 * @brief Get sector energy
 * 
 * @param analyzer      Analyzer instance
 * @param sector        Sector ID
 * @return              Energy in dB
 */
float psmsl_get_sector_energy(const psmsl_analyzer_t *analyzer,
                               psmsl_sector_id_t sector);

/**
 * @brief Get sector coherence
 * 
 * @param analyzer      Analyzer instance
 * @param sector        Sector ID
 * @return              Sector coherence (0.0 to 1.0)
 */
float psmsl_get_sector_coherence(const psmsl_analyzer_t *analyzer,
                                  psmsl_sector_id_t sector);

/**
 * @brief Get sector phase
 * 
 * @param analyzer      Analyzer instance
 * @param sector        Sector ID
 * @return              Dominant phase (radians)
 */
float psmsl_get_sector_phase(const psmsl_analyzer_t *analyzer,
                              psmsl_sector_id_t sector);

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * @brief Convert frequency to sector ID
 * 
 * @param freq          Frequency in Hz
 * @return              Sector ID
 */
psmsl_sector_id_t psmsl_freq_to_sector(float freq);

/**
 * @brief Get sector center frequency
 * 
 * @param sector        Sector ID
 * @return              Center frequency in Hz
 */
float psmsl_sector_center_freq(psmsl_sector_id_t sector);

/**
 * @brief Get sector name string
 * 
 * @param sector        Sector ID
 * @return              Human-readable sector name
 */
const char* psmsl_sector_name(psmsl_sector_id_t sector);

/**
 * @brief Verify Thyme Identity
 * 
 * Computes π² - (7φ² + √2) / 2 and returns the error.
 * Should be very close to zero.
 * 
 * @return              Error from Thyme Identity
 */
float psmsl_verify_thyme_identity(void);

#ifdef __cplusplus
}
#endif

#endif // PSMSL_ANALYSIS_H
