/**
 * @file psmsl_analysis.c
 * @brief PSMSL (Phi-Scaled Mirrored Semantic Lattice) Analysis Implementation
 * 
 * This implementation replaces FFT-based spectral analysis with covariance
 * geometry based on the Leibniz-Bocker framework.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "psmsl_analysis.h"
#include "psmsl_eigen.h"
#include "psmsl_grassmann.h"
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Sector Names
// =============================================================================

static const char* sector_names[PSMSL_NUM_SECTORS] = {
    "Foundation",   // 20-80 Hz
    "Structure",    // 80-200 Hz
    "Body",         // 200-500 Hz
    "Presence",     // 500-2000 Hz
    "Clarity",      // 2000-5000 Hz
    "Air",          // 5000-10000 Hz
    "Extension"     // 10000-20000 Hz
};

// =============================================================================
// Private Functions: Covariance Computation
// =============================================================================

/**
 * @brief Compute covariance matrix from input samples
 * 
 * Maps multi-channel time-domain samples to k-dimensional covariance space.
 * Uses φ-scaled time embedding for temporal structure.
 */
static void compute_covariance(psmsl_analyzer_t *analyzer)
{
    const uint32_t n = analyzer->window_size;
    const uint8_t channels = analyzer->num_channels;
    
    // Embedding dimension per channel
    const uint32_t embed_dim = PSMSL_K_DIMENSIONS / channels;
    
    // Clear covariance matrix
    memset(analyzer->covariance, 0, sizeof(analyzer->covariance));
    
    // Build embedded vectors and compute covariance
    for (uint32_t t = embed_dim; t < n; t++) {
        float embedded[PSMSL_K_DIMENSIONS];
        
        // Create embedded vector with φ-scaled delays
        for (uint8_t ch = 0; ch < channels; ch++) {
            for (uint32_t d = 0; d < embed_dim; d++) {
                // φ-scaled delay: delay = floor(d * φ)
                uint32_t delay = (uint32_t)(d * PSMSL_PHI);
                if (delay >= t) delay = t - 1;
                
                uint32_t idx = ch * embed_dim + d;
                embedded[idx] = analyzer->input_buffer[ch][t - delay];
            }
        }
        
        // Accumulate outer product: C += x * x^T
        for (uint32_t i = 0; i < PSMSL_K_DIMENSIONS; i++) {
            for (uint32_t j = i; j < PSMSL_K_DIMENSIONS; j++) {
                float prod = embedded[i] * embedded[j];
                analyzer->covariance[i][j] += prod;
                if (i != j) {
                    analyzer->covariance[j][i] += prod;  // Symmetric
                }
            }
        }
    }
    
    // Normalize by number of samples
    float norm = 1.0f / (float)(n - embed_dim);
    for (uint32_t i = 0; i < PSMSL_K_DIMENSIONS; i++) {
        for (uint32_t j = 0; j < PSMSL_K_DIMENSIONS; j++) {
            analyzer->covariance[i][j] *= norm;
        }
    }
}

/**
 * @brief Compute Leibniz-Bocker diagnostics from eigenvalues
 */
static void compute_diagnostics(psmsl_analyzer_t *analyzer)
{
    lb_diagnostics_t *diag = &analyzer->result.diagnostics;
    
    // Sum of eigenvalues (total variance)
    float total_variance = 0.0f;
    for (uint32_t i = 0; i < PSMSL_K_DIMENSIONS; i++) {
        total_variance += analyzer->eigenvalues[i];
    }
    
    if (total_variance < 1e-10f) {
        diag->coherence = 0.0f;
        diag->curvature = 0.0f;
        diag->residual = 1.0f;
        diag->stability = 1.0f;
        diag->novelty = 1.0f;
        return;
    }
    
    // Coherence (ρ): Effective dimensionality
    // Using participation ratio: (Σλ)² / Σλ²
    float sum_sq = 0.0f;
    for (uint32_t i = 0; i < PSMSL_K_DIMENSIONS; i++) {
        sum_sq += analyzer->eigenvalues[i] * analyzer->eigenvalues[i];
    }
    float effective_dim = (total_variance * total_variance) / (sum_sq + 1e-10f);
    diag->coherence = 1.0f - (effective_dim / PSMSL_K_DIMENSIONS);
    
    // Curvature (Ω): Rate of subspace rotation
    // Computed from principal angles between current and previous subspace
    diag->curvature = grassmann_compute_curvature(
        analyzer->subspace_prev,
        analyzer->subspace_curr,
        PSMSL_K_DIMENSIONS,
        PSMSL_NUM_SECTORS
    );
    
    // Residual (r): Unexplained variance
    // Fraction of variance not captured by top-k eigenvalues
    float captured = 0.0f;
    for (uint32_t i = 0; i < PSMSL_NUM_SECTORS; i++) {
        captured += analyzer->eigenvalues[i];
    }
    diag->residual = 1.0f - (captured / total_variance);
    
    // Derived metrics
    diag->stability = 1.0f / (1.0f + diag->curvature);
    diag->novelty = diag->residual * (1.0f - diag->coherence);
}

/**
 * @brief Map eigenspace to semantic sectors
 */
static void compute_sector_results(psmsl_analyzer_t *analyzer)
{
    psmsl_result_t *result = &analyzer->result;
    
    // Total eigenvalue sum for normalization
    float total_eigen = 0.0f;
    for (uint32_t i = 0; i < PSMSL_K_DIMENSIONS; i++) {
        total_eigen += analyzer->eigenvalues[i];
    }
    
    // Compute per-sector metrics
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        psmsl_sector_result_t *sector = &result->sectors[s];
        
        // Project eigenvalues onto sector using projection matrix
        float sector_energy = 0.0f;
        float weighted_phase = 0.0f;
        float phase_weight = 0.0f;
        
        for (uint32_t k = 0; k < PSMSL_K_DIMENSIONS; k++) {
            float proj = analyzer->sector_projection[s][k];
            float contrib = proj * analyzer->eigenvalues[k];
            sector_energy += contrib;
            
            // Phase from eigenvector (simplified)
            weighted_phase += proj * analyzer->eigenvectors[k][0];
            phase_weight += fabsf(proj);
        }
        
        sector->energy_linear = sector_energy;
        sector->energy_db = 10.0f * log10f(sector_energy + 1e-10f);
        sector->phase = atan2f(weighted_phase, phase_weight + 1e-10f);
        
        // Sector coherence: concentration of energy in this sector
        sector->eigenvalue_sum = sector_energy;
        sector->eigenvalue_ratio = sector_energy / (total_eigen + 1e-10f);
        sector->sector_coherence = sector->eigenvalue_ratio * PSMSL_NUM_SECTORS;
        if (sector->sector_coherence > 1.0f) sector->sector_coherence = 1.0f;
        
        // φ-scaled recursion depth
        sector->phi_depth = logf(sector_energy + 1.0f) / logf(PSMSL_PHI);
        sector->phi_weight = powf(PSMSL_PHI, -(float)s);
    }
    
    // Compute summary metrics
    float weighted_freq = 0.0f;
    float total_energy = 0.0f;
    
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        float center = psmsl_sector_center_freq((psmsl_sector_id_t)s);
        float energy = result->sectors[s].energy_linear;
        weighted_freq += center * energy;
        total_energy += energy;
    }
    
    result->total_energy_db = 10.0f * log10f(total_energy + 1e-10f);
    result->spectral_centroid = weighted_freq / (total_energy + 1e-10f);
    
    // Spectral spread (standard deviation)
    float variance = 0.0f;
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        float center = psmsl_sector_center_freq((psmsl_sector_id_t)s);
        float energy = result->sectors[s].energy_linear;
        float diff = center - result->spectral_centroid;
        variance += diff * diff * energy;
    }
    result->spectral_spread = sqrtf(variance / (total_energy + 1e-10f));
    
    // Spectral flatness (geometric mean / arithmetic mean)
    float log_sum = 0.0f;
    uint8_t valid_sectors = 0;
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        if (result->sectors[s].energy_linear > 1e-10f) {
            log_sum += logf(result->sectors[s].energy_linear);
            valid_sectors++;
        }
    }
    if (valid_sectors > 0) {
        float geo_mean = expf(log_sum / valid_sectors);
        float arith_mean = total_energy / valid_sectors;
        result->spectral_flatness = geo_mean / (arith_mean + 1e-10f);
    } else {
        result->spectral_flatness = 0.0f;
    }
}

/**
 * @brief Initialize sector projection matrix
 * 
 * Maps k-dimensional eigenspace to 7 semantic sectors based on
 * frequency characteristics and φ-scaling.
 */
static void init_sector_projection(psmsl_analyzer_t *analyzer)
{
    // Initialize with φ-scaled weights
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        for (uint32_t k = 0; k < PSMSL_K_DIMENSIONS; k++) {
            // Base weight from sector-dimension correspondence
            float base = (k % PSMSL_NUM_SECTORS == s) ? 1.0f : 0.1f;
            
            // φ-scaled modulation
            float phi_factor = powf(PSMSL_PHI, -(float)abs((int)k - (int)(s * 3)));
            
            analyzer->sector_projection[s][k] = base * phi_factor;
        }
        
        // Normalize row
        float row_sum = 0.0f;
        for (uint32_t k = 0; k < PSMSL_K_DIMENSIONS; k++) {
            row_sum += analyzer->sector_projection[s][k];
        }
        for (uint32_t k = 0; k < PSMSL_K_DIMENSIONS; k++) {
            analyzer->sector_projection[s][k] /= (row_sum + 1e-10f);
        }
    }
}

// =============================================================================
// Public API: Initialization
// =============================================================================

bool psmsl_init(psmsl_analyzer_t *analyzer, 
                float sample_rate, 
                uint8_t num_channels)
{
    if (!analyzer || num_channels == 0 || num_channels > PSMSL_MAX_CHANNELS) {
        return false;
    }
    
    memset(analyzer, 0, sizeof(psmsl_analyzer_t));
    
    analyzer->sample_rate = sample_rate;
    analyzer->num_channels = num_channels;
    analyzer->window_size = PSMSL_WINDOW_SIZE;
    analyzer->overlap = PSMSL_OVERLAP;
    
    // Initialize sector projection matrix
    init_sector_projection(analyzer);
    
    analyzer->initialized = true;
    
    return true;
}

void psmsl_reset(psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return;
    
    memset(analyzer->input_buffer, 0, sizeof(analyzer->input_buffer));
    analyzer->input_index = 0;
    
    memset(analyzer->covariance, 0, sizeof(analyzer->covariance));
    memset(analyzer->eigenvalues, 0, sizeof(analyzer->eigenvalues));
    memset(analyzer->eigenvectors, 0, sizeof(analyzer->eigenvectors));
    
    memset(analyzer->history, 0, sizeof(analyzer->history));
    analyzer->history_index = 0;
    analyzer->history_count = 0;
    
    memset(&analyzer->result, 0, sizeof(psmsl_result_t));
    analyzer->frame_count = 0;
}

bool psmsl_calibrate(psmsl_analyzer_t *analyzer,
                     const float *const *ref_data,
                     uint32_t frames)
{
    if (!analyzer || !ref_data) return false;
    
    // TODO: Implement calibration
    // - Collect statistics from reference signal
    // - Adjust sector projection matrix
    // - Store calibration data
    
    analyzer->calibrated = true;
    return true;
}

// =============================================================================
// Public API: Analysis
// =============================================================================

bool psmsl_feed(psmsl_analyzer_t *analyzer,
                const float *const *samples,
                uint32_t count)
{
    if (!analyzer || !analyzer->initialized || !samples) {
        return false;
    }
    
    bool result_ready = false;
    
    for (uint32_t i = 0; i < count; i++) {
        // Add samples to buffer
        for (uint8_t ch = 0; ch < analyzer->num_channels; ch++) {
            analyzer->input_buffer[ch][analyzer->input_index] = samples[ch][i];
        }
        
        analyzer->input_index++;
        
        // Check if buffer is full
        if (analyzer->input_index >= analyzer->window_size) {
            result_ready = true;
            
            // Shift buffer by overlap amount
            uint32_t shift = analyzer->window_size - analyzer->overlap;
            for (uint8_t ch = 0; ch < analyzer->num_channels; ch++) {
                memmove(analyzer->input_buffer[ch],
                        analyzer->input_buffer[ch] + shift,
                        analyzer->overlap * sizeof(float));
            }
            analyzer->input_index = analyzer->overlap;
        }
    }
    
    return result_ready;
}

bool psmsl_process(psmsl_analyzer_t *analyzer)
{
    if (!analyzer || !analyzer->initialized) {
        return false;
    }
    
    // Save previous covariance and subspace for curvature computation
    memcpy(analyzer->covariance_prev, analyzer->covariance, 
           sizeof(analyzer->covariance));
    memcpy(analyzer->subspace_prev, analyzer->subspace_curr,
           sizeof(analyzer->subspace_curr));
    
    // Step 1: Compute covariance matrix
    compute_covariance(analyzer);
    
    // Step 2: Eigendecomposition
    eigen_decompose(analyzer->covariance,
                    analyzer->eigenvalues,
                    analyzer->eigenvectors,
                    PSMSL_K_DIMENSIONS);
    
    // Step 3: Update Grassmann subspace
    grassmann_update_subspace(analyzer->eigenvectors,
                               analyzer->subspace_curr,
                               PSMSL_K_DIMENSIONS,
                               PSMSL_NUM_SECTORS);
    
    // Step 4: Compute Leibniz-Bocker diagnostics
    compute_diagnostics(analyzer);
    
    // Step 5: Map to semantic sectors
    compute_sector_results(analyzer);
    
    // Update result metadata
    analyzer->result.timestamp_ms = analyzer->frame_count * 
                                     (analyzer->window_size - analyzer->overlap) * 
                                     1000 / (uint32_t)analyzer->sample_rate;
    analyzer->result.frame_count = analyzer->frame_count;
    analyzer->result.valid = true;
    
    // Store in history
    analyzer->history[analyzer->history_index] = analyzer->result;
    analyzer->history_index = (analyzer->history_index + 1) % PSMSL_HISTORY_SIZE;
    if (analyzer->history_count < PSMSL_HISTORY_SIZE) {
        analyzer->history_count++;
    }
    
    analyzer->frame_count++;
    
    return true;
}

const psmsl_result_t* psmsl_get_result(const psmsl_analyzer_t *analyzer)
{
    if (!analyzer || !analyzer->result.valid) {
        return NULL;
    }
    return &analyzer->result;
}

// =============================================================================
// Public API: Diagnostic Accessors
// =============================================================================

float psmsl_get_coherence(const psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    return analyzer->result.diagnostics.coherence;
}

float psmsl_get_curvature(const psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 0.0f;
    return analyzer->result.diagnostics.curvature;
}

float psmsl_get_residual(const psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return 1.0f;
    return analyzer->result.diagnostics.residual;
}

const lb_diagnostics_t* psmsl_get_diagnostics(const psmsl_analyzer_t *analyzer)
{
    if (!analyzer) return NULL;
    return &analyzer->result.diagnostics;
}

// =============================================================================
// Public API: Sector Accessors
// =============================================================================

float psmsl_get_sector_energy(const psmsl_analyzer_t *analyzer,
                               psmsl_sector_id_t sector)
{
    if (!analyzer || sector >= PSMSL_NUM_SECTORS) return -100.0f;
    return analyzer->result.sectors[sector].energy_db;
}

float psmsl_get_sector_coherence(const psmsl_analyzer_t *analyzer,
                                  psmsl_sector_id_t sector)
{
    if (!analyzer || sector >= PSMSL_NUM_SECTORS) return 0.0f;
    return analyzer->result.sectors[sector].sector_coherence;
}

float psmsl_get_sector_phase(const psmsl_analyzer_t *analyzer,
                              psmsl_sector_id_t sector)
{
    if (!analyzer || sector >= PSMSL_NUM_SECTORS) return 0.0f;
    return analyzer->result.sectors[sector].phase;
}

// =============================================================================
// Public API: Utility Functions
// =============================================================================

psmsl_sector_id_t psmsl_freq_to_sector(float freq)
{
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        if (freq >= PSMSL_SECTOR_FREQ_LOW[s] && freq < PSMSL_SECTOR_FREQ_HIGH[s]) {
            return (psmsl_sector_id_t)s;
        }
    }
    
    // Default to extension for very high frequencies
    if (freq >= PSMSL_SECTOR_FREQ_HIGH[PSMSL_NUM_SECTORS - 1]) {
        return PSMSL_SECTOR_EXTENSION;
    }
    
    // Default to foundation for very low frequencies
    return PSMSL_SECTOR_FOUNDATION;
}

float psmsl_sector_center_freq(psmsl_sector_id_t sector)
{
    if (sector >= PSMSL_NUM_SECTORS) return 1000.0f;
    
    // Geometric mean of sector boundaries
    return sqrtf(PSMSL_SECTOR_FREQ_LOW[sector] * PSMSL_SECTOR_FREQ_HIGH[sector]);
}

const char* psmsl_sector_name(psmsl_sector_id_t sector)
{
    if (sector >= PSMSL_NUM_SECTORS) return "Unknown";
    return sector_names[sector];
}

float psmsl_verify_thyme_identity(void)
{
    // Thyme Identity: π² = (7φ² + √2) / 2
    float lhs = PSMSL_PI_SQUARED;
    float rhs = (7.0f * PSMSL_PHI_SQUARED + PSMSL_SQRT2) / 2.0f;
    return lhs - rhs;
}
