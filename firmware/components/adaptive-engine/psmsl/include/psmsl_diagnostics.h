/**
 * @file psmsl_diagnostics.h
 * @brief Extended diagnostic commands for PSMSL firmware
 * 
 * Provides comprehensive diagnostic capabilities for:
 * - Hardware verification (mics, DAC, signal path)
 * - Acoustic analysis (noise floor, room modes, RT60)
 * - PSMSL metrics (coherence, curvature, residual)
 * - Sector analysis and corrections
 * - Real-time monitoring and logging
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef PSMSL_DIAGNOSTICS_H
#define PSMSL_DIAGNOSTICS_H

#include <stdint.h>
#include <stdbool.h>
#include "psmsl_analysis.h"

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

#define DIAG_MAX_MODES          16      // Maximum room modes to detect
#define DIAG_HISTORY_SIZE       256     // Convergence history samples
#define DIAG_FFT_SIZE           2048    // FFT size for spectral analysis

// =============================================================================
// Diagnostic Data Structures
// =============================================================================

/**
 * @brief Microphone diagnostic data
 */
typedef struct {
    uint8_t channel;
    float level_db;
    float noise_floor_db;
    float peak_db;
    float dc_offset;
    bool clipping;
    bool connected;
} diag_mic_status_t;

/**
 * @brief DAC diagnostic data
 */
typedef struct {
    bool initialized;
    bool running;
    float output_level_db;
    uint32_t sample_rate;
    uint8_t bit_depth;
    uint32_t underruns;
    uint32_t overruns;
} diag_dac_status_t;

/**
 * @brief Room mode data
 */
typedef struct {
    float frequency;        // Mode frequency (Hz)
    float q_factor;         // Quality factor
    float magnitude_db;     // Magnitude relative to average
    float bandwidth;        // 3dB bandwidth (Hz)
    uint8_t type;           // 0=axial, 1=tangential, 2=oblique
} diag_room_mode_t;

/**
 * @brief Room acoustic analysis
 */
typedef struct {
    // Noise floor
    float noise_floor_db;
    float noise_floor_weighted_db;  // A-weighted
    
    // Signal analysis
    float signal_level_db;
    float snr_db;
    float thd_percent;              // Total harmonic distortion
    
    // Room characteristics
    float rt60_estimate;            // Reverberation time (seconds)
    float schroeder_freq;           // Schroeder frequency (Hz)
    float clarity_c50;              // C50 clarity metric
    float definition_d50;           // D50 definition metric
    
    // Room modes
    uint8_t num_modes;
    diag_room_mode_t modes[DIAG_MAX_MODES];
    
    // Frequency response
    float response_deviation_db;    // Max deviation from flat
    float bass_ratio;               // Low freq energy ratio
    float treble_ratio;             // High freq energy ratio
} diag_room_analysis_t;

/**
 * @brief PSMSL diagnostic snapshot
 */
typedef struct {
    // Timestamp
    uint32_t timestamp_ms;
    uint32_t frame_count;
    
    // Leibniz-Bocker diagnostics
    float coherence;
    float curvature;
    float residual;
    float stability;
    float novelty;
    
    // Convergence
    float convergence;
    float convergence_rate;         // Change per second
    
    // Sector data
    float sector_energy[PSMSL_NUM_SECTORS];
    float sector_coherence[PSMSL_NUM_SECTORS];
    float sector_correction[PSMSL_NUM_SECTORS];
    
    // Eigenspace
    float eigenvalues[PSMSL_EMBED_DIM];
    float effective_rank;
    
    // Summary
    float spectral_centroid;
    float spectral_spread;
    float spectral_flatness;
    float total_energy_db;
} diag_psmsl_snapshot_t;

/**
 * @brief Convergence history
 */
typedef struct {
    uint32_t count;
    uint32_t start_time_ms;
    float convergence[DIAG_HISTORY_SIZE];
    float coherence[DIAG_HISTORY_SIZE];
    float curvature[DIAG_HISTORY_SIZE];
    uint32_t timestamps[DIAG_HISTORY_SIZE];
} diag_convergence_history_t;

/**
 * @brief System health status
 */
typedef struct {
    // CPU/Memory
    uint32_t free_heap;
    uint32_t min_free_heap;
    float cpu_usage_percent;
    
    // Audio
    uint32_t audio_buffer_level;
    uint32_t audio_underruns;
    uint32_t audio_overruns;
    float audio_latency_ms;
    
    // Processing
    uint32_t process_time_us;
    uint32_t max_process_time_us;
    float process_load_percent;
    
    // Errors
    uint32_t error_count;
    uint32_t warning_count;
    char last_error[64];
} diag_system_health_t;

// =============================================================================
// Diagnostic Functions
// =============================================================================

/**
 * @brief Initialize diagnostic system
 */
bool diag_init(void);

/**
 * @brief Get microphone status
 */
void diag_get_mic_status(diag_mic_status_t *status, uint8_t channel);

/**
 * @brief Get all microphone levels
 */
void diag_get_mic_levels(float *levels, uint8_t *num_channels);

/**
 * @brief Get DAC status
 */
void diag_get_dac_status(diag_dac_status_t *status);

/**
 * @brief Measure noise floor
 * @param duration_ms Measurement duration
 */
float diag_measure_noise_floor(uint32_t duration_ms);

/**
 * @brief Measure signal level
 */
float diag_measure_signal_level(void);

/**
 * @brief Analyze room acoustics
 * @param analysis Output analysis structure
 * @param use_sweep If true, run frequency sweep; otherwise use current signal
 */
void diag_analyze_room(diag_room_analysis_t *analysis, bool use_sweep);

/**
 * @brief Detect room modes
 * @param modes Output array of detected modes
 * @param max_modes Maximum modes to detect
 * @return Number of modes detected
 */
uint8_t diag_detect_room_modes(diag_room_mode_t *modes, uint8_t max_modes);

/**
 * @brief Estimate RT60 reverberation time
 */
float diag_estimate_rt60(void);

/**
 * @brief Get current PSMSL snapshot
 */
void diag_get_psmsl_snapshot(diag_psmsl_snapshot_t *snapshot);

/**
 * @brief Get sector energies
 */
void diag_get_sector_energies(float *energies);

/**
 * @brief Get applied corrections
 */
void diag_get_corrections(float *corrections);

/**
 * @brief Get convergence history
 */
void diag_get_convergence_history(diag_convergence_history_t *history);

/**
 * @brief Clear convergence history
 */
void diag_clear_history(void);

/**
 * @brief Get system health status
 */
void diag_get_system_health(diag_system_health_t *health);

/**
 * @brief Run self-test
 * @return Bitmask of test results (0 = all passed)
 */
uint32_t diag_run_self_test(void);

// =============================================================================
// Output Formatting
// =============================================================================

/**
 * @brief Print mic status to serial
 */
void diag_print_mic_status(void);

/**
 * @brief Print DAC status to serial
 */
void diag_print_dac_status(void);

/**
 * @brief Print noise floor measurement
 */
void diag_print_noise_floor(void);

/**
 * @brief Print signal level
 */
void diag_print_signal_level(void);

/**
 * @brief Print room mode analysis
 */
void diag_print_room_modes(void);

/**
 * @brief Print sector analysis
 */
void diag_print_sectors(void);

/**
 * @brief Print applied corrections
 */
void diag_print_corrections(void);

/**
 * @brief Print PSMSL snapshot
 */
void diag_print_psmsl_snapshot(void);

/**
 * @brief Print system health
 */
void diag_print_system_health(void);

/**
 * @brief Print full diagnostic report
 */
void diag_print_full_report(void);

// =============================================================================
// JSON Output
// =============================================================================

/**
 * @brief Output PSMSL snapshot as JSON
 */
void diag_json_psmsl_snapshot(void);

/**
 * @brief Output room analysis as JSON
 */
void diag_json_room_analysis(void);

/**
 * @brief Output system health as JSON
 */
void diag_json_system_health(void);

/**
 * @brief Output full status as JSON
 */
void diag_json_full_status(void);

// =============================================================================
// Serial Command Handler
// =============================================================================

/**
 * @brief Process diagnostic command
 * @param cmd Command string (e.g., "mic_levels", "noise_floor", "sectors")
 * @return true if command was recognized
 */
bool diag_process_command(const char *cmd);

/**
 * @brief Print diagnostic help
 */
void diag_print_help(void);

#ifdef __cplusplus
}
#endif

#endif // PSMSL_DIAGNOSTICS_H
