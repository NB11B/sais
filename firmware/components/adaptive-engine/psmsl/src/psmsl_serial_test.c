/**
 * @file psmsl_serial_test.c
 * @brief Serial command interface implementation for PSMSL testing
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "psmsl_serial_test.h"
#include "psmsl_analysis.h"
#include "psmsl_eigen.h"
#include "psmsl_grassmann.h"
#include "psmsl_config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ESP-IDF includes (conditional for host testing)
#ifdef ESP_PLATFORM
#include "esp_timer.h"
#include "driver/uart.h"
#include "esp_log.h"
#define TAG "PSMSL_TEST"
#else
// Host simulation
#include <time.h>
static uint64_t esp_timer_get_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000ULL + ts.tv_nsec / 1000;
}
#define ESP_LOGI(tag, fmt, ...) printf("[%s] " fmt "\n", tag, ##__VA_ARGS__)
#define TAG "PSMSL_TEST"
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Static Variables
// =============================================================================

static psmsl_analyzer_t s_analyzer;
static bool s_initialized = false;
static bool s_monitoring = false;
static uint32_t s_monitor_interval_ms = 100;
static uint32_t s_test_counter = 0;

static char s_cmd_buffer[PSMSL_TEST_CMD_MAX_LEN];
static uint32_t s_cmd_index = 0;

// =============================================================================
// Test Signal Generation
// =============================================================================

static void generate_sine(float *buffer, uint32_t samples, float freq, float sample_rate)
{
    for (uint32_t i = 0; i < samples; i++) {
        float t = (float)i / sample_rate;
        buffer[i] = sinf(2.0f * M_PI * freq * t);
    }
}

static void generate_multi_sine(float *buffer, uint32_t samples, float sample_rate)
{
    // Generate multiple frequencies: 100, 440, 1000, 4000 Hz
    float freqs[] = {100.0f, 440.0f, 1000.0f, 4000.0f};
    float amps[] = {0.3f, 0.3f, 0.25f, 0.15f};
    
    memset(buffer, 0, samples * sizeof(float));
    
    for (int f = 0; f < 4; f++) {
        for (uint32_t i = 0; i < samples; i++) {
            float t = (float)i / sample_rate;
            buffer[i] += amps[f] * sinf(2.0f * M_PI * freqs[f] * t);
        }
    }
}

static void generate_sweep(float *buffer, uint32_t samples, float sample_rate)
{
    // Logarithmic sweep from 20 Hz to 20 kHz
    float f0 = 20.0f;
    float f1 = 20000.0f;
    float duration = (float)samples / sample_rate;
    
    for (uint32_t i = 0; i < samples; i++) {
        float t = (float)i / sample_rate;
        float freq = f0 * powf(f1 / f0, t / duration);
        float phase = 2.0f * M_PI * f0 * duration / logf(f1 / f0) * 
                      (powf(f1 / f0, t / duration) - 1.0f);
        buffer[i] = sinf(phase);
    }
}

static void generate_noise(float *buffer, uint32_t samples)
{
    for (uint32_t i = 0; i < samples; i++) {
        buffer[i] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
    }
}

static void generate_room_sim(float *buffer, uint32_t samples, float sample_rate)
{
    // Simulate room modes at typical frequencies
    float modes[] = {35.0f, 50.0f, 70.0f, 100.0f, 140.0f};
    float amps[] = {0.4f, 0.35f, 0.3f, 0.2f, 0.15f};
    float decays[] = {0.95f, 0.93f, 0.90f, 0.85f, 0.80f};
    
    memset(buffer, 0, samples * sizeof(float));
    
    for (int m = 0; m < 5; m++) {
        float envelope = 1.0f;
        for (uint32_t i = 0; i < samples; i++) {
            float t = (float)i / sample_rate;
            buffer[i] += envelope * amps[m] * sinf(2.0f * M_PI * modes[m] * t);
            envelope *= decays[m];
            if (envelope < 0.001f) break;
        }
    }
}

// =============================================================================
// Test Execution
// =============================================================================

bool psmsl_serial_test_run(psmsl_test_signal_t signal_type,
                           float freq,
                           uint32_t duration_ms,
                           psmsl_test_result_t *result)
{
    if (!s_initialized || !result) return false;
    
    memset(result, 0, sizeof(psmsl_test_result_t));
    result->test_id = ++s_test_counter;
    result->signal_type = signal_type;
    result->signal_freq = freq;
    
    // Calculate samples needed
    float sample_rate = s_analyzer.sample_rate;
    uint32_t samples = (uint32_t)(sample_rate * duration_ms / 1000.0f);
    if (samples > PSMSL_WINDOW_SIZE) samples = PSMSL_WINDOW_SIZE;
    
    // Generate test signal
    float test_buffer[PSMSL_WINDOW_SIZE];
    
    switch (signal_type) {
        case PSMSL_TEST_SIGNAL_SINE:
            generate_sine(test_buffer, samples, freq, sample_rate);
            break;
        case PSMSL_TEST_SIGNAL_MULTI_SINE:
            generate_multi_sine(test_buffer, samples, sample_rate);
            break;
        case PSMSL_TEST_SIGNAL_SWEEP:
            generate_sweep(test_buffer, samples, sample_rate);
            break;
        case PSMSL_TEST_SIGNAL_NOISE:
            generate_noise(test_buffer, samples);
            break;
        case PSMSL_TEST_SIGNAL_ROOM_SIM:
            generate_room_sim(test_buffer, samples, sample_rate);
            break;
        default:
            generate_sine(test_buffer, samples, 1000.0f, sample_rate);
            break;
    }
    
    // Reset analyzer
    psmsl_reset(&s_analyzer);
    
    // Feed samples (duplicate to all channels)
    float *channel_ptrs[PSMSL_MAX_CHANNELS];
    for (int c = 0; c < s_analyzer.num_channels; c++) {
        channel_ptrs[c] = test_buffer;
    }
    
    // Time the processing
    uint64_t start_time = esp_timer_get_time();
    
    psmsl_feed(&s_analyzer, (const float *const *)channel_ptrs, samples);
    psmsl_process(&s_analyzer);
    
    uint64_t end_time = esp_timer_get_time();
    result->processing_time_us = (uint32_t)(end_time - start_time);
    
    // Get results
    const psmsl_result_t *psmsl_result = psmsl_get_result(&s_analyzer);
    
    if (!psmsl_result || !psmsl_result->valid) {
        result->passed = false;
        snprintf(result->error_msg, sizeof(result->error_msg), "Invalid PSMSL result");
        return false;
    }
    
    // Copy diagnostics
    result->coherence = psmsl_result->diagnostics.coherence;
    result->curvature = psmsl_result->diagnostics.curvature;
    result->residual = psmsl_result->diagnostics.residual;
    result->stability = psmsl_result->diagnostics.stability;
    result->novelty = psmsl_result->diagnostics.novelty;
    
    // Copy sector data
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        result->sector_energy[s] = psmsl_result->sectors[s].energy_db;
        result->sector_coherence[s] = psmsl_result->sectors[s].sector_coherence;
    }
    
    // Copy summary
    result->spectral_centroid = psmsl_result->spectral_centroid;
    result->spectral_spread = psmsl_result->spectral_spread;
    result->total_energy_db = psmsl_result->total_energy_db;
    
    // Validate results based on signal type
    result->passed = true;
    
    switch (signal_type) {
        case PSMSL_TEST_SIGNAL_SINE:
            // Sine wave should have high coherence
            if (result->coherence < 0.5f) {
                result->passed = false;
                snprintf(result->error_msg, sizeof(result->error_msg), 
                         "Low coherence for sine: %.3f", result->coherence);
            }
            break;
            
        case PSMSL_TEST_SIGNAL_NOISE:
            // Noise should have lower coherence than sine
            if (result->coherence > 0.9f) {
                result->passed = false;
                snprintf(result->error_msg, sizeof(result->error_msg), 
                         "High coherence for noise: %.3f", result->coherence);
            }
            break;
            
        default:
            // Basic sanity checks
            if (result->coherence < 0.0f || result->coherence > 1.0f) {
                result->passed = false;
                snprintf(result->error_msg, sizeof(result->error_msg), 
                         "Coherence out of range: %.3f", result->coherence);
            }
            break;
    }
    
    return result->passed;
}

// =============================================================================
// Output Functions
// =============================================================================

void psmsl_serial_test_print_state(void)
{
    if (!s_initialized) {
        printf("ERROR: PSMSL not initialized\n");
        return;
    }
    
    const psmsl_result_t *result = psmsl_get_result(&s_analyzer);
    
    printf("\n");
    printf("=== PSMSL State ===\n");
    printf("\n");
    printf("Leibniz-Bocker Diagnostics:\n");
    printf("  Coherence (ρ):  %.4f\n", result->diagnostics.coherence);
    printf("  Curvature (Ω):  %.4f\n", result->diagnostics.curvature);
    printf("  Residual (r):   %.4f\n", result->diagnostics.residual);
    printf("  Stability:      %.4f\n", result->diagnostics.stability);
    printf("  Novelty:        %.4f\n", result->diagnostics.novelty);
    printf("\n");
    printf("Sector Energies:\n");
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        printf("  %-12s: %7.2f dB  (coherence: %.3f)\n",
               psmsl_get_sector_name(s),
               result->sectors[s].energy_db,
               result->sectors[s].sector_coherence);
    }
    printf("\n");
    printf("Summary:\n");
    printf("  Total Energy:      %.2f dB\n", result->total_energy_db);
    printf("  Spectral Centroid: %.1f Hz\n", result->spectral_centroid);
    printf("  Spectral Spread:   %.1f Hz\n", result->spectral_spread);
    printf("  Spectral Flatness: %.4f\n", result->spectral_flatness);
    printf("\n");
}

void psmsl_serial_test_print_json(void)
{
    if (!s_initialized) {
        printf("{\"error\": \"PSMSL not initialized\"}\n");
        return;
    }
    
    const psmsl_result_t *result = psmsl_get_result(&s_analyzer);
    
    printf("{");
    printf("\"coherence\":%.4f,", result->diagnostics.coherence);
    printf("\"curvature\":%.4f,", result->diagnostics.curvature);
    printf("\"residual\":%.4f,", result->diagnostics.residual);
    printf("\"stability\":%.4f,", result->diagnostics.stability);
    printf("\"novelty\":%.4f,", result->diagnostics.novelty);
    printf("\"sectors\":[");
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        printf("{\"name\":\"%s\",\"energy\":%.2f,\"coherence\":%.3f}",
               psmsl_get_sector_name(s),
               result->sectors[s].energy_db,
               result->sectors[s].sector_coherence);
        if (s < PSMSL_NUM_SECTORS - 1) printf(",");
    }
    printf("],");
    printf("\"total_energy\":%.2f,", result->total_energy_db);
    printf("\"centroid\":%.1f,", result->spectral_centroid);
    printf("\"spread\":%.1f,", result->spectral_spread);
    printf("\"flatness\":%.4f", result->spectral_flatness);
    printf("}\n");
}

static void print_test_result(const psmsl_test_result_t *result)
{
    printf("\n");
    printf("--- Test #%lu ---\n", (unsigned long)result->test_id);
    printf("Signal: %d, Freq: %.1f Hz\n", result->signal_type, result->signal_freq);
    printf("Processing time: %lu us\n", (unsigned long)result->processing_time_us);
    printf("Coherence: %.4f, Curvature: %.4f, Residual: %.4f\n",
           result->coherence, result->curvature, result->residual);
    printf("Centroid: %.1f Hz, Spread: %.1f Hz\n",
           result->spectral_centroid, result->spectral_spread);
    printf("Result: %s\n", result->passed ? "PASS" : "FAIL");
    if (!result->passed) {
        printf("Error: %s\n", result->error_msg);
    }
    printf("\n");
}

// =============================================================================
// Test Suite
// =============================================================================

uint32_t psmsl_serial_test_run_all(void)
{
    printf("\n");
    printf("========================================\n");
    printf("PSMSL Full Test Suite\n");
    printf("========================================\n");
    
    uint32_t passed = 0;
    uint32_t total = 0;
    psmsl_test_result_t result;
    
    // Test 1: Thyme Identity
    printf("\n[Test 1] Thyme Identity Verification\n");
    float phi_sq = PSMSL_PHI_SQUARED;
    float sqrt2 = PSMSL_SQRT2;
    float pi_sq = PSMSL_PI_SQUARED;
    float computed = (7.0f * phi_sq + sqrt2) / 2.0f;
    float error = fabsf(computed - pi_sq);
    printf("  π² = %.6f\n", pi_sq);
    printf("  (7φ² + √2)/2 = %.6f\n", computed);
    printf("  Error = %.6e\n", error);
    if (error < 1e-4f) {
        printf("  Result: PASS\n");
        passed++;
    } else {
        printf("  Result: FAIL\n");
    }
    total++;
    
    // Test 2: Sine wave coherence
    printf("\n[Test 2] Sine Wave (1 kHz) - High Coherence Expected\n");
    psmsl_serial_test_run(PSMSL_TEST_SIGNAL_SINE, 1000.0f, 100, &result);
    print_test_result(&result);
    if (result.passed) passed++;
    total++;
    
    // Test 3: Noise coherence
    printf("\n[Test 3] White Noise - Low Coherence Expected\n");
    psmsl_serial_test_run(PSMSL_TEST_SIGNAL_NOISE, 0.0f, 100, &result);
    print_test_result(&result);
    if (result.passed) passed++;
    total++;
    
    // Test 4: Multi-frequency
    printf("\n[Test 4] Multi-Frequency Signal\n");
    psmsl_serial_test_run(PSMSL_TEST_SIGNAL_MULTI_SINE, 0.0f, 100, &result);
    print_test_result(&result);
    if (result.passed) passed++;
    total++;
    
    // Test 5: Frequency sweep
    printf("\n[Test 5] Frequency Sweep (20 Hz - 20 kHz)\n");
    psmsl_serial_test_run(PSMSL_TEST_SIGNAL_SWEEP, 0.0f, 100, &result);
    print_test_result(&result);
    if (result.passed) passed++;
    total++;
    
    // Test 6: Room simulation
    printf("\n[Test 6] Simulated Room Modes\n");
    psmsl_serial_test_run(PSMSL_TEST_SIGNAL_ROOM_SIM, 0.0f, 100, &result);
    print_test_result(&result);
    if (result.passed) passed++;
    total++;
    
    // Test 7: Sector mapping
    printf("\n[Test 7] Sector Frequency Mapping\n");
    bool sector_pass = true;
    struct { float freq; uint8_t expected; } sector_tests[] = {
        {50.0f, PSMSL_SECTOR_FOUNDATION},
        {150.0f, PSMSL_SECTOR_STRUCTURE},
        {350.0f, PSMSL_SECTOR_BODY},
        {1000.0f, PSMSL_SECTOR_PRESENCE},
        {3500.0f, PSMSL_SECTOR_CLARITY},
        {7500.0f, PSMSL_SECTOR_AIR},
        {15000.0f, PSMSL_SECTOR_EXTENSION},
    };
    for (int i = 0; i < 7; i++) {
        uint8_t sector = psmsl_freq_to_sector(sector_tests[i].freq);
        printf("  %.0f Hz -> %s: %s\n", 
               sector_tests[i].freq,
               psmsl_get_sector_name(sector),
               sector == sector_tests[i].expected ? "OK" : "FAIL");
        if (sector != sector_tests[i].expected) sector_pass = false;
    }
    printf("  Result: %s\n", sector_pass ? "PASS" : "FAIL");
    if (sector_pass) passed++;
    total++;
    
    // Test 8: Processing speed
    printf("\n[Test 8] Processing Speed\n");
    psmsl_serial_test_run(PSMSL_TEST_SIGNAL_SINE, 440.0f, 100, &result);
    printf("  Processing time: %lu us\n", (unsigned long)result.processing_time_us);
    printf("  Target: < 10000 us (10 ms)\n");
    bool speed_pass = result.processing_time_us < 10000;
    printf("  Result: %s\n", speed_pass ? "PASS" : "FAIL");
    if (speed_pass) passed++;
    total++;
    
    // Summary
    printf("\n========================================\n");
    printf("Test Summary: %lu/%lu passed\n", (unsigned long)passed, (unsigned long)total);
    printf("========================================\n\n");
    
    return passed;
}

// =============================================================================
// Command Processing
// =============================================================================

static void process_command(const char *cmd)
{
    // Skip leading whitespace
    while (*cmd == ' ' || *cmd == '\t') cmd++;
    
    if (strlen(cmd) == 0) return;
    
    if (strcmp(cmd, "help") == 0) {
        printf("\n");
        printf("PSMSL Test Commands:\n");
        printf("  help              - Show this help\n");
        printf("  status            - Show current PSMSL state\n");
        printf("  json              - Output state as JSON\n");
        printf("  test sine <freq>  - Test with sine wave\n");
        printf("  test sweep        - Test with frequency sweep\n");
        printf("  test noise        - Test with white noise\n");
        printf("  test room         - Test with simulated room\n");
        printf("  test all          - Run full test suite\n");
        printf("  monitor <ms>      - Start continuous monitoring\n");
        printf("  stop              - Stop monitoring\n");
        printf("  thyme             - Verify Thyme Identity\n");
        printf("  reset             - Reset PSMSL analyzer\n");
        printf("\n");
    }
    else if (strcmp(cmd, "status") == 0) {
        psmsl_serial_test_print_state();
    }
    else if (strcmp(cmd, "json") == 0) {
        psmsl_serial_test_print_json();
    }
    else if (strncmp(cmd, "test sine ", 10) == 0) {
        float freq = atof(cmd + 10);
        if (freq <= 0) freq = 1000.0f;
        psmsl_test_result_t result;
        psmsl_serial_test_run(PSMSL_TEST_SIGNAL_SINE, freq, 100, &result);
        print_test_result(&result);
    }
    else if (strcmp(cmd, "test sweep") == 0) {
        psmsl_test_result_t result;
        psmsl_serial_test_run(PSMSL_TEST_SIGNAL_SWEEP, 0.0f, 100, &result);
        print_test_result(&result);
    }
    else if (strcmp(cmd, "test noise") == 0) {
        psmsl_test_result_t result;
        psmsl_serial_test_run(PSMSL_TEST_SIGNAL_NOISE, 0.0f, 100, &result);
        print_test_result(&result);
    }
    else if (strcmp(cmd, "test room") == 0) {
        psmsl_test_result_t result;
        psmsl_serial_test_run(PSMSL_TEST_SIGNAL_ROOM_SIM, 0.0f, 100, &result);
        print_test_result(&result);
    }
    else if (strcmp(cmd, "test all") == 0) {
        psmsl_serial_test_run_all();
    }
    else if (strncmp(cmd, "monitor ", 8) == 0) {
        uint32_t interval = atoi(cmd + 8);
        if (interval < 10) interval = 100;
        psmsl_serial_test_start_monitor(interval);
    }
    else if (strcmp(cmd, "stop") == 0) {
        psmsl_serial_test_stop_monitor();
    }
    else if (strcmp(cmd, "thyme") == 0) {
        printf("\nThyme Identity Verification:\n");
        printf("  π² = (7φ² + √2) / 2\n");
        printf("  φ = %.10f\n", PSMSL_PHI);
        printf("  φ² = %.10f\n", PSMSL_PHI_SQUARED);
        printf("  √2 = %.10f\n", PSMSL_SQRT2);
        printf("  π² = %.10f\n", PSMSL_PI_SQUARED);
        float computed = (7.0f * PSMSL_PHI_SQUARED + PSMSL_SQRT2) / 2.0f;
        printf("  Computed: %.10f\n", computed);
        printf("  Error: %.10e\n", fabsf(computed - PSMSL_PI_SQUARED));
        printf("\n");
    }
    else if (strcmp(cmd, "reset") == 0) {
        psmsl_reset(&s_analyzer);
        printf("PSMSL analyzer reset\n");
    }
    else {
        printf("Unknown command: %s\n", cmd);
        printf("Type 'help' for available commands\n");
    }
}

// =============================================================================
// Initialization and Main Loop
// =============================================================================

bool psmsl_serial_test_init(void)
{
    // Initialize PSMSL analyzer
    if (!psmsl_init(&s_analyzer, 48000.0f, 2)) {
        printf("ERROR: Failed to initialize PSMSL analyzer\n");
        return false;
    }
    
    s_initialized = true;
    s_cmd_index = 0;
    
    printf("\n");
    printf("========================================\n");
    printf("PSMSL Serial Test Interface\n");
    printf("Adaptive Crossover Firmware\n");
    printf("Copyright (c) Nathanael J. Bocker, 2026\n");
    printf("========================================\n");
    printf("Type 'help' for available commands\n");
    printf("\n");
    printf("> ");
    fflush(stdout);
    
    return true;
}

void psmsl_serial_test_process(void)
{
    // Read characters from serial (platform-specific)
#ifdef ESP_PLATFORM
    uint8_t c;
    while (uart_read_bytes(UART_NUM_0, &c, 1, 0) > 0) {
#else
    // For host testing, use stdin
    int c;
    while ((c = getchar()) != EOF) {
#endif
        if (c == '\n' || c == '\r') {
            s_cmd_buffer[s_cmd_index] = '\0';
            printf("\n");
            process_command(s_cmd_buffer);
            s_cmd_index = 0;
            printf("> ");
            fflush(stdout);
        }
        else if (c == '\b' || c == 127) {
            if (s_cmd_index > 0) {
                s_cmd_index--;
                printf("\b \b");
                fflush(stdout);
            }
        }
        else if (s_cmd_index < PSMSL_TEST_CMD_MAX_LEN - 1) {
            s_cmd_buffer[s_cmd_index++] = (char)c;
            printf("%c", c);
            fflush(stdout);
        }
#ifndef ESP_PLATFORM
        break;  // Non-blocking for host
#endif
    }
}

void psmsl_serial_test_start_monitor(uint32_t interval_ms)
{
    s_monitoring = true;
    s_monitor_interval_ms = interval_ms;
    printf("Monitoring started (interval: %lu ms)\n", (unsigned long)interval_ms);
    printf("Press 'stop' to end monitoring\n");
}

void psmsl_serial_test_stop_monitor(void)
{
    s_monitoring = false;
    printf("Monitoring stopped\n");
}
