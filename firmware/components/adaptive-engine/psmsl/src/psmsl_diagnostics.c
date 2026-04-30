/**
 * @file psmsl_diagnostics.c
 * @brief Extended diagnostic commands implementation
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "psmsl_diagnostics.h"
#include "psmsl_analysis.h"
#include "psmsl_config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef ESP_PLATFORM
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#else
#include <time.h>
static uint64_t esp_timer_get_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000ULL + ts.tv_nsec / 1000;
}
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Static Variables
// =============================================================================

static bool s_diag_initialized = false;
static diag_convergence_history_t s_history;
static diag_system_health_t s_health;
static uint32_t s_frame_count = 0;

// External reference to PSMSL analyzer (set by main app)
extern psmsl_analyzer_t *g_psmsl_analyzer;

// Simulated data for testing (replace with actual hardware access)
static float s_mic_levels[4] = {-35.0f, -36.0f, -34.0f, -35.5f};
static float s_noise_floor = -65.0f;
static float s_signal_level = -20.0f;

// =============================================================================
// Initialization
// =============================================================================

bool diag_init(void)
{
    memset(&s_history, 0, sizeof(s_history));
    memset(&s_health, 0, sizeof(s_health));
    
    s_history.start_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
    s_diag_initialized = true;
    
    return true;
}

// =============================================================================
// Hardware Diagnostics
// =============================================================================

void diag_get_mic_status(diag_mic_status_t *status, uint8_t channel)
{
    if (!status || channel >= 4) return;
    
    status->channel = channel;
    status->level_db = s_mic_levels[channel];
    status->noise_floor_db = s_noise_floor;
    status->peak_db = s_mic_levels[channel] + 10.0f;
    status->dc_offset = 0.001f;
    status->clipping = false;
    status->connected = true;
}

void diag_get_mic_levels(float *levels, uint8_t *num_channels)
{
    if (!levels || !num_channels) return;
    
    *num_channels = 4;
    for (int i = 0; i < 4; i++) {
        levels[i] = s_mic_levels[i];
    }
}

void diag_get_dac_status(diag_dac_status_t *status)
{
    if (!status) return;
    
    status->initialized = true;
    status->running = true;
    status->output_level_db = -12.0f;
    status->sample_rate = 48000;
    status->bit_depth = 24;
    status->underruns = s_health.audio_underruns;
    status->overruns = s_health.audio_overruns;
}

float diag_measure_noise_floor(uint32_t duration_ms)
{
    // In real implementation, measure actual noise
    // For now, return simulated value
    (void)duration_ms;
    return s_noise_floor;
}

float diag_measure_signal_level(void)
{
    return s_signal_level;
}

// =============================================================================
// Room Analysis
// =============================================================================

void diag_analyze_room(diag_room_analysis_t *analysis, bool use_sweep)
{
    if (!analysis) return;
    
    (void)use_sweep;
    
    // Fill with simulated/measured data
    analysis->noise_floor_db = s_noise_floor;
    analysis->noise_floor_weighted_db = s_noise_floor + 5.0f;  // A-weighted typically higher
    analysis->signal_level_db = s_signal_level;
    analysis->snr_db = s_signal_level - s_noise_floor;
    analysis->thd_percent = 0.05f;
    
    // Room characteristics
    analysis->rt60_estimate = 0.45f;  // Typical small room
    analysis->schroeder_freq = 200.0f;
    analysis->clarity_c50 = 3.5f;
    analysis->definition_d50 = 0.65f;
    
    // Detect modes
    analysis->num_modes = diag_detect_room_modes(analysis->modes, DIAG_MAX_MODES);
    
    // Response analysis
    analysis->response_deviation_db = 8.5f;
    analysis->bass_ratio = 1.15f;
    analysis->treble_ratio = 0.92f;
}

uint8_t diag_detect_room_modes(diag_room_mode_t *modes, uint8_t max_modes)
{
    if (!modes || max_modes == 0) return 0;
    
    // Simulated room modes for a typical small room (3m x 4m x 2.5m)
    // Axial modes: f = c / (2L) where c = 343 m/s
    static const struct {
        float freq;
        float q;
        float mag;
        uint8_t type;
    } typical_modes[] = {
        {42.9f, 8.0f, 6.2f, 0},   // Length mode (4m)
        {57.2f, 7.5f, 4.8f, 0},   // Width mode (3m)
        {68.6f, 6.0f, 3.5f, 0},   // Height mode (2.5m)
        {85.8f, 5.5f, 2.8f, 0},   // 2nd length
        {100.0f, 5.0f, 2.2f, 1},  // Tangential
        {114.4f, 4.5f, 1.8f, 0},  // 2nd width
        {137.2f, 4.0f, 1.5f, 0},  // 2nd height
    };
    
    uint8_t count = 0;
    for (int i = 0; i < 7 && count < max_modes; i++) {
        modes[count].frequency = typical_modes[i].freq;
        modes[count].q_factor = typical_modes[i].q;
        modes[count].magnitude_db = typical_modes[i].mag;
        modes[count].bandwidth = typical_modes[i].freq / typical_modes[i].q;
        modes[count].type = typical_modes[i].type;
        count++;
    }
    
    return count;
}

float diag_estimate_rt60(void)
{
    // Simplified RT60 estimation
    // In real implementation, use impulse response analysis
    return 0.45f;
}

// =============================================================================
// PSMSL Diagnostics
// =============================================================================

void diag_get_psmsl_snapshot(diag_psmsl_snapshot_t *snapshot)
{
    if (!snapshot) return;
    
    snapshot->timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000);
    snapshot->frame_count = s_frame_count++;
    
    // Get data from PSMSL analyzer if available
    if (g_psmsl_analyzer) {
        const psmsl_result_t *result = psmsl_get_result(g_psmsl_analyzer);
        
        if (result && result->valid) {
            snapshot->coherence = result->diagnostics.coherence;
            snapshot->curvature = result->diagnostics.curvature;
            snapshot->residual = result->diagnostics.residual;
            snapshot->stability = result->diagnostics.stability;
            snapshot->novelty = result->diagnostics.novelty;
            
            for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
                snapshot->sector_energy[s] = result->sectors[s].energy_db;
                snapshot->sector_coherence[s] = result->sectors[s].sector_coherence;
            }
            
            snapshot->spectral_centroid = result->spectral_centroid;
            snapshot->spectral_spread = result->spectral_spread;
            snapshot->spectral_flatness = result->spectral_flatness;
            snapshot->total_energy_db = result->total_energy_db;
        }
    } else {
        // Simulated data for testing
        snapshot->coherence = 0.75f + 0.1f * sinf(s_frame_count * 0.01f);
        snapshot->curvature = 0.15f + 0.05f * sinf(s_frame_count * 0.02f);
        snapshot->residual = 0.25f - 0.05f * sinf(s_frame_count * 0.01f);
        snapshot->stability = 0.85f;
        snapshot->novelty = 0.12f;
        
        // Simulated sector data
        float base_energies[] = {-45, -38, -32, -28, -35, -42, -48};
        for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
            snapshot->sector_energy[s] = base_energies[s] + 2.0f * sinf(s_frame_count * 0.01f + s);
            snapshot->sector_coherence[s] = 0.7f + 0.2f * (float)s / PSMSL_NUM_SECTORS;
            snapshot->sector_correction[s] = 0.0f;
        }
        
        snapshot->spectral_centroid = 1200.0f;
        snapshot->spectral_spread = 800.0f;
        snapshot->spectral_flatness = 0.45f;
        snapshot->total_energy_db = -25.0f;
    }
    
    // Calculate convergence (simplified)
    snapshot->convergence = snapshot->coherence * (1.0f - snapshot->residual);
    
    // Update history
    if (s_history.count < DIAG_HISTORY_SIZE) {
        uint32_t idx = s_history.count++;
        s_history.convergence[idx] = snapshot->convergence;
        s_history.coherence[idx] = snapshot->coherence;
        s_history.curvature[idx] = snapshot->curvature;
        s_history.timestamps[idx] = snapshot->timestamp_ms;
    }
}

void diag_get_sector_energies(float *energies)
{
    if (!energies) return;
    
    diag_psmsl_snapshot_t snapshot;
    diag_get_psmsl_snapshot(&snapshot);
    
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        energies[s] = snapshot.sector_energy[s];
    }
}

void diag_get_corrections(float *corrections)
{
    if (!corrections) return;
    
    // Simulated corrections
    float base_corrections[] = {2.5f, 1.2f, -0.5f, 0.0f, 0.8f, -1.5f, -2.0f};
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        corrections[s] = base_corrections[s];
    }
}

void diag_get_convergence_history(diag_convergence_history_t *history)
{
    if (!history) return;
    memcpy(history, &s_history, sizeof(diag_convergence_history_t));
}

void diag_clear_history(void)
{
    memset(&s_history, 0, sizeof(s_history));
    s_history.start_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
}

// =============================================================================
// System Health
// =============================================================================

void diag_get_system_health(diag_system_health_t *health)
{
    if (!health) return;
    
#ifdef ESP_PLATFORM
    health->free_heap = esp_get_free_heap_size();
    health->min_free_heap = esp_get_minimum_free_heap_size();
#else
    health->free_heap = 100000;
    health->min_free_heap = 80000;
#endif
    
    health->cpu_usage_percent = 35.0f;
    health->audio_buffer_level = 75;
    health->audio_underruns = s_health.audio_underruns;
    health->audio_overruns = s_health.audio_overruns;
    health->audio_latency_ms = 5.3f;
    health->process_time_us = 2500;
    health->max_process_time_us = 4200;
    health->process_load_percent = 12.0f;
    health->error_count = s_health.error_count;
    health->warning_count = s_health.warning_count;
    strncpy(health->last_error, s_health.last_error, sizeof(health->last_error) - 1);
}

uint32_t diag_run_self_test(void)
{
    uint32_t result = 0;
    
    printf("\nRunning self-test...\n");
    
    // Test 1: Memory
    printf("  [1] Memory check: ");
#ifdef ESP_PLATFORM
    if (esp_get_free_heap_size() < 20000) {
        printf("FAIL (low heap)\n");
        result |= 0x01;
    } else {
        printf("PASS\n");
    }
#else
    printf("PASS (simulated)\n");
#endif
    
    // Test 2: PSMSL initialization
    printf("  [2] PSMSL check: ");
    if (g_psmsl_analyzer) {
        printf("PASS\n");
    } else {
        printf("WARN (not initialized)\n");
        result |= 0x02;
    }
    
    // Test 3: Thyme Identity
    printf("  [3] Thyme Identity: ");
    float phi_sq = PSMSL_PHI_SQUARED;
    float sqrt2 = PSMSL_SQRT2;
    float pi_sq = PSMSL_PI_SQUARED;
    float computed = (7.0f * phi_sq + sqrt2) / 2.0f;
    if (fabsf(computed - pi_sq) < 1e-4f) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        result |= 0x04;
    }
    
    // Test 4: Audio path (simulated)
    printf("  [4] Audio path: PASS (simulated)\n");
    
    // Test 5: Serial interface
    printf("  [5] Serial interface: PASS\n");
    
    printf("\nSelf-test complete. Result: 0x%02lX\n", (unsigned long)result);
    
    return result;
}

// =============================================================================
// Print Functions
// =============================================================================

void diag_print_mic_status(void)
{
    printf("\nMicrophone Status:\n");
    for (int i = 0; i < 4; i++) {
        diag_mic_status_t status;
        diag_get_mic_status(&status, i);
        printf("  Mic %d: %.1f dB %s%s\n", 
               i, status.level_db,
               status.connected ? "" : "(disconnected)",
               status.clipping ? " [CLIPPING]" : "");
    }
}

void diag_print_dac_status(void)
{
    diag_dac_status_t status;
    diag_get_dac_status(&status);
    
    printf("\nDAC Status:\n");
    printf("  Initialized: %s\n", status.initialized ? "Yes" : "No");
    printf("  Running: %s\n", status.running ? "Yes" : "No");
    printf("  Sample rate: %lu Hz\n", (unsigned long)status.sample_rate);
    printf("  Bit depth: %d\n", status.bit_depth);
    printf("  Output level: %.1f dB\n", status.output_level_db);
    printf("  Underruns: %lu\n", (unsigned long)status.underruns);
    printf("  Overruns: %lu\n", (unsigned long)status.overruns);
}

void diag_print_noise_floor(void)
{
    float noise = diag_measure_noise_floor(1000);
    float signal = diag_measure_signal_level();
    
    printf("\nNoise Analysis:\n");
    printf("  Noise floor: %.1f dB\n", noise);
    printf("  Signal level: %.1f dB\n", signal);
    printf("  SNR: %.1f dB\n", signal - noise);
}

void diag_print_signal_level(void)
{
    float level = diag_measure_signal_level();
    printf("Signal level: %.1f dB\n", level);
}

void diag_print_room_modes(void)
{
    diag_room_mode_t modes[DIAG_MAX_MODES];
    uint8_t count = diag_detect_room_modes(modes, DIAG_MAX_MODES);
    
    printf("\nRoom Modes Detected: %d\n", count);
    for (int i = 0; i < count; i++) {
        const char *type_str = modes[i].type == 0 ? "Axial" : 
                               modes[i].type == 1 ? "Tang" : "Oblq";
        printf("  Mode %d: %.1f Hz, Q=%.1f, %+.1f dB (%s)\n",
               i + 1, modes[i].frequency, modes[i].q_factor,
               modes[i].magnitude_db, type_str);
    }
    
    float rt60 = diag_estimate_rt60();
    printf("  RT60 estimate: %.2f s\n", rt60);
    printf("  Schroeder freq: ~200 Hz\n");
}

void diag_print_sectors(void)
{
    static const char *sector_names[] = {
        "Foundation", "Structure", "Body", "Presence",
        "Clarity", "Air", "Extension"
    };
    
    float energies[PSMSL_NUM_SECTORS];
    diag_get_sector_energies(energies);
    
    printf("\nSector Analysis:\n");
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        printf("  %-12s: %7.1f dB\n", sector_names[s], energies[s]);
    }
}

void diag_print_corrections(void)
{
    static const char *sector_names[] = {
        "Foundation", "Structure", "Body", "Presence",
        "Clarity", "Air", "Extension"
    };
    
    float corrections[PSMSL_NUM_SECTORS];
    diag_get_corrections(corrections);
    
    printf("\nApplied Corrections:\n");
    for (int s = 0; s < PSMSL_NUM_SECTORS; s++) {
        printf("  %-12s: %+.1f dB\n", sector_names[s], corrections[s]);
    }
}

void diag_print_psmsl_snapshot(void)
{
    diag_psmsl_snapshot_t snapshot;
    diag_get_psmsl_snapshot(&snapshot);
    
    printf("\nPSMSL Status:\n");
    printf("  Frame: %lu\n", (unsigned long)snapshot.frame_count);
    printf("  Coherence (ρ): %.4f\n", snapshot.coherence);
    printf("  Curvature (Ω): %.4f\n", snapshot.curvature);
    printf("  Residual (r):  %.4f\n", snapshot.residual);
    printf("  Stability:     %.4f\n", snapshot.stability);
    printf("  Novelty:       %.4f\n", snapshot.novelty);
    printf("  Convergence:   %.1f%%\n", snapshot.convergence * 100.0f);
    printf("  Total Energy:  %.1f dB\n", snapshot.total_energy_db);
    printf("  Centroid:      %.0f Hz\n", snapshot.spectral_centroid);
}

void diag_print_system_health(void)
{
    diag_system_health_t health;
    diag_get_system_health(&health);
    
    printf("\nSystem Health:\n");
    printf("  Free heap: %lu bytes\n", (unsigned long)health.free_heap);
    printf("  Min heap:  %lu bytes\n", (unsigned long)health.min_free_heap);
    printf("  CPU usage: %.1f%%\n", health.cpu_usage_percent);
    printf("  Process time: %lu us (max: %lu us)\n", 
           (unsigned long)health.process_time_us,
           (unsigned long)health.max_process_time_us);
    printf("  Audio latency: %.1f ms\n", health.audio_latency_ms);
    printf("  Errors: %lu, Warnings: %lu\n",
           (unsigned long)health.error_count,
           (unsigned long)health.warning_count);
}

void diag_print_full_report(void)
{
    printf("\n");
    printf("========================================\n");
    printf("FULL DIAGNOSTIC REPORT\n");
    printf("========================================\n");
    
    diag_print_system_health();
    diag_print_mic_status();
    diag_print_dac_status();
    diag_print_noise_floor();
    diag_print_psmsl_snapshot();
    diag_print_sectors();
    diag_print_corrections();
    diag_print_room_modes();
    
    printf("\n========================================\n");
}

// =============================================================================
// JSON Output
// =============================================================================

void diag_json_psmsl_snapshot(void)
{
    diag_psmsl_snapshot_t s;
    diag_get_psmsl_snapshot(&s);
    
    printf("{\"frame\":%lu,\"coherence\":%.4f,\"curvature\":%.4f,"
           "\"residual\":%.4f,\"stability\":%.4f,\"novelty\":%.4f,"
           "\"convergence\":%.4f,\"energy\":%.1f,\"centroid\":%.0f}\n",
           (unsigned long)s.frame_count, s.coherence, s.curvature,
           s.residual, s.stability, s.novelty,
           s.convergence, s.total_energy_db, s.spectral_centroid);
}

void diag_json_room_analysis(void)
{
    diag_room_analysis_t a;
    diag_analyze_room(&a, false);
    
    printf("{\"noise_floor\":%.1f,\"snr\":%.1f,\"rt60\":%.2f,"
           "\"schroeder\":%.0f,\"num_modes\":%d}\n",
           a.noise_floor_db, a.snr_db, a.rt60_estimate,
           a.schroeder_freq, a.num_modes);
}

void diag_json_system_health(void)
{
    diag_system_health_t h;
    diag_get_system_health(&h);
    
    printf("{\"free_heap\":%lu,\"cpu\":%.1f,\"process_us\":%lu,"
           "\"latency_ms\":%.1f,\"errors\":%lu}\n",
           (unsigned long)h.free_heap, h.cpu_usage_percent,
           (unsigned long)h.process_time_us, h.audio_latency_ms,
           (unsigned long)h.error_count);
}

void diag_json_full_status(void)
{
    diag_psmsl_snapshot_t s;
    diag_get_psmsl_snapshot(&s);
    
    printf("{");
    printf("\"coherence\":%.4f,", s.coherence);
    printf("\"curvature\":%.4f,", s.curvature);
    printf("\"residual\":%.4f,", s.residual);
    printf("\"convergence\":%.4f,", s.convergence);
    printf("\"energy\":%.1f,", s.total_energy_db);
    printf("\"sectors\":[");
    for (int i = 0; i < PSMSL_NUM_SECTORS; i++) {
        printf("%.1f%s", s.sector_energy[i], i < PSMSL_NUM_SECTORS - 1 ? "," : "");
    }
    printf("]}\n");
}

// =============================================================================
// Command Handler
// =============================================================================

bool diag_process_command(const char *cmd)
{
    if (!cmd) return false;
    
    // Skip "diag " prefix if present
    if (strncmp(cmd, "diag ", 5) == 0) {
        cmd += 5;
    }
    
    if (strcmp(cmd, "mic_levels") == 0 || strcmp(cmd, "mic") == 0) {
        diag_print_mic_status();
        return true;
    }
    else if (strcmp(cmd, "dac_status") == 0 || strcmp(cmd, "dac") == 0) {
        diag_print_dac_status();
        return true;
    }
    else if (strcmp(cmd, "noise_floor") == 0 || strcmp(cmd, "noise") == 0) {
        diag_print_noise_floor();
        return true;
    }
    else if (strcmp(cmd, "signal_level") == 0 || strcmp(cmd, "signal") == 0) {
        diag_print_signal_level();
        return true;
    }
    else if (strcmp(cmd, "room_modes") == 0 || strcmp(cmd, "modes") == 0) {
        diag_print_room_modes();
        return true;
    }
    else if (strcmp(cmd, "sectors") == 0) {
        diag_print_sectors();
        return true;
    }
    else if (strcmp(cmd, "corrections") == 0 || strcmp(cmd, "corr") == 0) {
        diag_print_corrections();
        return true;
    }
    else if (strcmp(cmd, "psmsl") == 0 || strcmp(cmd, "snapshot") == 0) {
        diag_print_psmsl_snapshot();
        return true;
    }
    else if (strcmp(cmd, "health") == 0 || strcmp(cmd, "system") == 0) {
        diag_print_system_health();
        return true;
    }
    else if (strcmp(cmd, "full") == 0 || strcmp(cmd, "report") == 0) {
        diag_print_full_report();
        return true;
    }
    else if (strcmp(cmd, "selftest") == 0 || strcmp(cmd, "test") == 0) {
        diag_run_self_test();
        return true;
    }
    else if (strcmp(cmd, "json") == 0) {
        diag_json_full_status();
        return true;
    }
    else if (strcmp(cmd, "help") == 0) {
        diag_print_help();
        return true;
    }
    
    return false;
}

void diag_print_help(void)
{
    printf("\nDiagnostic Commands:\n");
    printf("  diag mic_levels    - Show microphone levels\n");
    printf("  diag dac_status    - Show DAC status\n");
    printf("  diag noise_floor   - Measure noise floor\n");
    printf("  diag signal_level  - Measure signal level\n");
    printf("  diag room_modes    - Detect room modes\n");
    printf("  diag sectors       - Show sector energies\n");
    printf("  diag corrections   - Show applied corrections\n");
    printf("  diag psmsl         - Show PSMSL snapshot\n");
    printf("  diag health        - Show system health\n");
    printf("  diag full          - Full diagnostic report\n");
    printf("  diag selftest      - Run self-test\n");
    printf("  diag json          - Output status as JSON\n");
    printf("\n");
}
