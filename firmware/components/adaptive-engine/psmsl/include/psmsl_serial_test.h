/**
 * @file psmsl_serial_test.h
 * @brief Serial command interface for PSMSL testing via USB
 * 
 * Provides a command-line interface over USB serial for:
 * - Running PSMSL analysis on test signals
 * - Viewing Leibniz-Bocker diagnostics in real-time
 * - Validating sector energy distribution
 * - Testing eigendecomposition and Grassmann operations
 * 
 * Usage: Connect via USB serial at 115200 baud, type 'help' for commands.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef PSMSL_SERIAL_TEST_H
#define PSMSL_SERIAL_TEST_H

#include <stdint.h>
#include <stdbool.h>
#include "psmsl_analysis.h"

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

#define PSMSL_TEST_BAUD_RATE        115200
#define PSMSL_TEST_CMD_MAX_LEN      128
#define PSMSL_TEST_OUTPUT_BUF_SIZE  1024

// =============================================================================
// Test Signal Types
// =============================================================================

typedef enum {
    PSMSL_TEST_SIGNAL_SINE,         // Single sine wave
    PSMSL_TEST_SIGNAL_MULTI_SINE,   // Multiple sine waves
    PSMSL_TEST_SIGNAL_SWEEP,        // Frequency sweep
    PSMSL_TEST_SIGNAL_NOISE,        // White noise
    PSMSL_TEST_SIGNAL_PINK_NOISE,   // Pink noise
    PSMSL_TEST_SIGNAL_IMPULSE,      // Impulse response
    PSMSL_TEST_SIGNAL_ROOM_SIM,     // Simulated room modes
} psmsl_test_signal_t;

// =============================================================================
// Test Result Structure
// =============================================================================

typedef struct {
    // Test identification
    uint32_t test_id;
    psmsl_test_signal_t signal_type;
    float signal_freq;
    
    // Leibniz-Bocker diagnostics
    float coherence;
    float curvature;
    float residual;
    float stability;
    float novelty;
    
    // Sector energies (dB)
    float sector_energy[PSMSL_NUM_SECTORS];
    float sector_coherence[PSMSL_NUM_SECTORS];
    
    // Summary metrics
    float spectral_centroid;
    float spectral_spread;
    float total_energy_db;
    
    // Timing
    uint32_t processing_time_us;
    
    // Validation
    bool passed;
    char error_msg[64];
} psmsl_test_result_t;

// =============================================================================
// Serial Test Interface
// =============================================================================

/**
 * @brief Initialize serial test interface
 * 
 * Sets up UART for USB serial communication and registers commands.
 * 
 * @return true on success
 */
bool psmsl_serial_test_init(void);

/**
 * @brief Process incoming serial commands
 * 
 * Call this periodically (e.g., in main loop) to handle commands.
 */
void psmsl_serial_test_process(void);

/**
 * @brief Run a specific test and output results
 * 
 * @param signal_type   Type of test signal to generate
 * @param freq          Frequency for sine-based signals (Hz)
 * @param duration_ms   Duration of test signal (ms)
 * @param result        Output test result
 * @return              true if test passed
 */
bool psmsl_serial_test_run(psmsl_test_signal_t signal_type,
                           float freq,
                           uint32_t duration_ms,
                           psmsl_test_result_t *result);

/**
 * @brief Run full test suite
 * 
 * Executes all built-in tests and reports results.
 * 
 * @return Number of tests passed
 */
uint32_t psmsl_serial_test_run_all(void);

/**
 * @brief Output current PSMSL state to serial
 * 
 * Prints current diagnostics in human-readable format.
 */
void psmsl_serial_test_print_state(void);

/**
 * @brief Output current PSMSL state as JSON
 * 
 * Prints current diagnostics in JSON format for parsing.
 */
void psmsl_serial_test_print_json(void);

/**
 * @brief Start continuous monitoring mode
 * 
 * Outputs diagnostics at specified interval until stopped.
 * 
 * @param interval_ms   Output interval in milliseconds
 */
void psmsl_serial_test_start_monitor(uint32_t interval_ms);

/**
 * @brief Stop continuous monitoring mode
 */
void psmsl_serial_test_stop_monitor(void);

// =============================================================================
// Command Handlers (Internal)
// =============================================================================

// These are registered automatically by psmsl_serial_test_init()
// Available commands:
//   help              - Show available commands
//   status            - Show current PSMSL state
//   json              - Output state as JSON
//   test sine <freq>  - Test with sine wave at frequency
//   test sweep        - Test with frequency sweep
//   test noise        - Test with white noise
//   test room         - Test with simulated room modes
//   test all          - Run full test suite
//   monitor <ms>      - Start continuous monitoring
//   stop              - Stop monitoring
//   eigen             - Test eigendecomposition
//   grassmann         - Test Grassmann operations
//   thyme             - Verify Thyme Identity
//   reset             - Reset PSMSL analyzer

#ifdef __cplusplus
}
#endif

#endif // PSMSL_SERIAL_TEST_H
