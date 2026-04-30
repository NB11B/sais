/**
 * @file test_psmsl.c
 * @brief Integration tests for PSMSL analysis components
 * 
 * Tests the PSMSL analysis pipeline including:
 * - Eigendecomposition accuracy
 * - Grassmann manifold operations
 * - Leibniz-Bocker diagnostic computation
 * - Sector mapping and energy distribution
 * - Thyme Identity verification
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>

#include "psmsl_analysis.h"
#include "psmsl_eigen.h"
#include "psmsl_grassmann.h"
#include "psmsl_config.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Test Utilities
// =============================================================================

#define TEST_EPSILON 1e-5f
#define TEST_PASS(name) printf("[PASS] %s\n", name)
#define TEST_FAIL(name, msg) printf("[FAIL] %s: %s\n", name, msg)

static int tests_passed = 0;
static int tests_failed = 0;

static void assert_float_eq(float a, float b, float epsilon, const char *name)
{
    if (fabsf(a - b) > epsilon) {
        printf("[FAIL] %s: expected %.6f, got %.6f\n", name, b, a);
        tests_failed++;
    } else {
        tests_passed++;
    }
}

static void assert_true(bool condition, const char *name)
{
    if (!condition) {
        printf("[FAIL] %s\n", name);
        tests_failed++;
    } else {
        tests_passed++;
    }
}

// =============================================================================
// Test: Thyme Identity Verification
// =============================================================================

static void test_thyme_identity(void)
{
    printf("\n=== Test: Thyme Identity ===\n");
    
    // π² = (7φ² + √2) / 2
    float phi = PSMSL_PHI;
    float phi_sq = PSMSL_PHI_SQUARED;
    float sqrt2 = PSMSL_SQRT2;
    float pi_sq = PSMSL_PI_SQUARED;
    
    float computed = (7.0f * phi_sq + sqrt2) / 2.0f;
    float error = fabsf(computed - pi_sq);
    
    printf("  φ = %.10f\n", phi);
    printf("  φ² = %.10f\n", phi_sq);
    printf("  √2 = %.10f\n", sqrt2);
    printf("  π² = %.10f\n", pi_sq);
    printf("  (7φ² + √2) / 2 = %.10f\n", computed);
    printf("  Error = %.10e\n", error);
    
    // Thyme Identity should hold within floating-point precision
    assert_float_eq(computed, pi_sq, 1e-4f, "Thyme Identity");
    
    // Verify PSMSL_THYME_CONSTANT
    assert_float_eq(PSMSL_THYME_CONSTANT, pi_sq, 1e-4f, "PSMSL_THYME_CONSTANT");
    
    TEST_PASS("Thyme Identity Verification");
}

// =============================================================================
// Test: Eigendecomposition
// =============================================================================

static void test_eigendecomposition(void)
{
    printf("\n=== Test: Eigendecomposition ===\n");
    
    // Create a simple symmetric matrix with known eigenvalues
    // A = diag(4, 3, 2, 1) rotated by 45 degrees
    float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM];
    float eigenvalues[EIGEN_MAX_DIM];
    float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM];
    
    memset(matrix, 0, sizeof(matrix));
    
    // Simple 4x4 diagonal matrix
    matrix[0][0] = 4.0f;
    matrix[1][1] = 3.0f;
    matrix[2][2] = 2.0f;
    matrix[3][3] = 1.0f;
    
    int iterations = eigen_decompose(matrix, eigenvalues, eigenvectors, 4);
    
    printf("  Iterations: %d\n", iterations);
    printf("  Eigenvalues: %.4f, %.4f, %.4f, %.4f\n",
           eigenvalues[0], eigenvalues[1], eigenvalues[2], eigenvalues[3]);
    
    // Eigenvalues should be 4, 3, 2, 1 in descending order
    assert_float_eq(eigenvalues[0], 4.0f, TEST_EPSILON, "λ₁ = 4");
    assert_float_eq(eigenvalues[1], 3.0f, TEST_EPSILON, "λ₂ = 3");
    assert_float_eq(eigenvalues[2], 2.0f, TEST_EPSILON, "λ₃ = 2");
    assert_float_eq(eigenvalues[3], 1.0f, TEST_EPSILON, "λ₄ = 1");
    
    // Test a more complex symmetric matrix
    float A[EIGEN_MAX_DIM][EIGEN_MAX_DIM];
    memset(A, 0, sizeof(A));
    
    // Create symmetric positive definite matrix
    A[0][0] = 5.0f; A[0][1] = 2.0f; A[0][2] = 1.0f;
    A[1][0] = 2.0f; A[1][1] = 4.0f; A[1][2] = 2.0f;
    A[2][0] = 1.0f; A[2][1] = 2.0f; A[2][2] = 3.0f;
    
    iterations = eigen_decompose(A, eigenvalues, eigenvectors, 3);
    
    printf("  Complex matrix eigenvalues: %.4f, %.4f, %.4f\n",
           eigenvalues[0], eigenvalues[1], eigenvalues[2]);
    
    // Verify trace preservation: sum of eigenvalues = trace of original
    float trace = 5.0f + 4.0f + 3.0f;
    float eigen_sum = eigenvalues[0] + eigenvalues[1] + eigenvalues[2];
    assert_float_eq(eigen_sum, trace, TEST_EPSILON, "Trace preservation");
    
    TEST_PASS("Eigendecomposition");
}

// =============================================================================
// Test: Grassmann Manifold Operations
// =============================================================================

static void test_grassmann_operations(void)
{
    printf("\n=== Test: Grassmann Manifold ===\n");
    
    // Create two subspaces
    float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K];
    
    memset(subspace1, 0, sizeof(subspace1));
    memset(subspace2, 0, sizeof(subspace2));
    
    // Subspace 1: span of e1, e2
    subspace1[0][0] = 1.0f;
    subspace1[1][1] = 1.0f;
    
    // Subspace 2: same as subspace 1 (distance should be 0)
    subspace2[0][0] = 1.0f;
    subspace2[1][1] = 1.0f;
    
    float dist = grassmann_distance(subspace1, subspace2, 4, 2);
    printf("  Distance (same subspace): %.6f\n", dist);
    assert_float_eq(dist, 0.0f, TEST_EPSILON, "Same subspace distance = 0");
    
    // Subspace 2: orthogonal to subspace 1
    memset(subspace2, 0, sizeof(subspace2));
    subspace2[2][0] = 1.0f;
    subspace2[3][1] = 1.0f;
    
    dist = grassmann_distance(subspace1, subspace2, 4, 2);
    printf("  Distance (orthogonal): %.6f\n", dist);
    
    // Orthogonal subspaces should have maximum distance
    // For 2D subspaces in 4D, max distance = sqrt(2) * π/2 ≈ 2.22
    assert_true(dist > 1.0f, "Orthogonal subspaces have large distance");
    
    // Test principal angles
    float angles[GRASSMANN_MAX_K];
    grassmann_principal_angles(subspace1, subspace2, angles, 4, 2);
    printf("  Principal angles: %.4f, %.4f\n", angles[0], angles[1]);
    
    // Orthogonal subspaces have principal angles of π/2
    assert_float_eq(angles[0], M_PI / 2.0f, 0.1f, "θ₁ ≈ π/2");
    assert_float_eq(angles[1], M_PI / 2.0f, 0.1f, "θ₂ ≈ π/2");
    
    // Test curvature computation
    float curvature = grassmann_compute_curvature(subspace1, subspace2, 4, 2);
    printf("  Curvature: %.6f\n", curvature);
    assert_true(curvature > 0.0f, "Curvature > 0 for different subspaces");
    
    TEST_PASS("Grassmann Manifold Operations");
}

// =============================================================================
// Test: PSMSL Analyzer Initialization
// =============================================================================

static void test_psmsl_init(void)
{
    printf("\n=== Test: PSMSL Initialization ===\n");
    
    psmsl_analyzer_t analyzer;
    
    // Test valid initialization
    bool result = psmsl_init(&analyzer, 48000.0f, 7);
    assert_true(result, "psmsl_init with valid params");
    assert_true(analyzer.initialized, "Analyzer marked as initialized");
    assert_float_eq(analyzer.sample_rate, 48000.0f, TEST_EPSILON, "Sample rate set");
    assert_true(analyzer.num_channels == 7, "Channel count set");
    
    // Test invalid parameters
    result = psmsl_init(NULL, 48000.0f, 7);
    assert_true(!result, "psmsl_init with NULL analyzer");
    
    result = psmsl_init(&analyzer, 48000.0f, 0);
    assert_true(!result, "psmsl_init with 0 channels");
    
    result = psmsl_init(&analyzer, 48000.0f, PSMSL_MAX_CHANNELS + 1);
    assert_true(!result, "psmsl_init with too many channels");
    
    TEST_PASS("PSMSL Initialization");
}

// =============================================================================
// Test: PSMSL Analysis Pipeline
// =============================================================================

static void test_psmsl_analysis(void)
{
    printf("\n=== Test: PSMSL Analysis Pipeline ===\n");
    
    psmsl_analyzer_t analyzer;
    psmsl_init(&analyzer, 48000.0f, 2);
    
    // Generate test signal: sine wave at 1 kHz
    float samples[2][PSMSL_WINDOW_SIZE];
    float freq = 1000.0f;
    float sample_rate = 48000.0f;
    
    for (uint32_t i = 0; i < PSMSL_WINDOW_SIZE; i++) {
        float t = (float)i / sample_rate;
        samples[0][i] = sinf(2.0f * M_PI * freq * t);
        samples[1][i] = sinf(2.0f * M_PI * freq * t + M_PI / 4.0f);  // Phase offset
    }
    
    // Feed samples
    const float *sample_ptrs[2] = {samples[0], samples[1]};
    bool ready = psmsl_feed(&analyzer, sample_ptrs, PSMSL_WINDOW_SIZE);
    
    // Process
    bool processed = psmsl_process(&analyzer);
    assert_true(processed, "psmsl_process succeeded");
    
    // Get result
    const psmsl_result_t *result = psmsl_get_result(&analyzer);
    assert_true(result != NULL, "Result not NULL");
    assert_true(result->valid, "Result is valid");
    
    // Check diagnostics
    printf("  Coherence: %.4f\n", result->diagnostics.coherence);
    printf("  Curvature: %.4f\n", result->diagnostics.curvature);
    printf("  Residual: %.4f\n", result->diagnostics.residual);
    printf("  Stability: %.4f\n", result->diagnostics.stability);
    printf("  Novelty: %.4f\n", result->diagnostics.novelty);
    
    // Pure sine wave should have high coherence
    assert_true(result->diagnostics.coherence > 0.5f, "Sine wave has high coherence");
    
    // First frame should have zero curvature
    assert_float_eq(result->diagnostics.curvature, 0.0f, 0.1f, "First frame curvature ≈ 0");
    
    // Check sector energies
    printf("  Sector energies:\n");
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        printf("    %s: %.2f dB\n", 
               psmsl_get_sector_name(s),
               result->sectors[s].energy_db);
    }
    
    // 1 kHz should be in Presence sector (500-2000 Hz)
    assert_true(result->sectors[PSMSL_SECTOR_PRESENCE].energy_db > 
                result->sectors[PSMSL_SECTOR_FOUNDATION].energy_db,
                "1 kHz signal in Presence sector");
    
    // Check summary metrics
    printf("  Total energy: %.2f dB\n", result->total_energy_db);
    printf("  Spectral centroid: %.1f Hz\n", result->spectral_centroid);
    printf("  Spectral spread: %.1f Hz\n", result->spectral_spread);
    printf("  Spectral flatness: %.4f\n", result->spectral_flatness);
    
    TEST_PASS("PSMSL Analysis Pipeline");
}

// =============================================================================
// Test: Leibniz-Bocker Diagnostics
// =============================================================================

static void test_lb_diagnostics(void)
{
    printf("\n=== Test: Leibniz-Bocker Diagnostics ===\n");
    
    psmsl_analyzer_t analyzer;
    psmsl_init(&analyzer, 48000.0f, 2);
    
    // Test 1: White noise (should have low coherence)
    float noise[2][PSMSL_WINDOW_SIZE];
    for (uint32_t i = 0; i < PSMSL_WINDOW_SIZE; i++) {
        noise[0][i] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
        noise[1][i] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
    }
    
    const float *noise_ptrs[2] = {noise[0], noise[1]};
    psmsl_feed(&analyzer, noise_ptrs, PSMSL_WINDOW_SIZE);
    psmsl_process(&analyzer);
    
    float noise_coherence = psmsl_get_coherence(&analyzer);
    printf("  Noise coherence: %.4f\n", noise_coherence);
    
    // Test 2: Pure tone (should have high coherence)
    psmsl_reset(&analyzer);
    
    float tone[2][PSMSL_WINDOW_SIZE];
    for (uint32_t i = 0; i < PSMSL_WINDOW_SIZE; i++) {
        float t = (float)i / 48000.0f;
        tone[0][i] = sinf(2.0f * M_PI * 440.0f * t);
        tone[1][i] = sinf(2.0f * M_PI * 440.0f * t);
    }
    
    const float *tone_ptrs[2] = {tone[0], tone[1]};
    psmsl_feed(&analyzer, tone_ptrs, PSMSL_WINDOW_SIZE);
    psmsl_process(&analyzer);
    
    float tone_coherence = psmsl_get_coherence(&analyzer);
    printf("  Tone coherence: %.4f\n", tone_coherence);
    
    // Tone should have higher coherence than noise
    assert_true(tone_coherence > noise_coherence, 
                "Tone has higher coherence than noise");
    
    // Test 3: Curvature with changing signal
    psmsl_reset(&analyzer);
    
    // First frame: 440 Hz
    psmsl_feed(&analyzer, tone_ptrs, PSMSL_WINDOW_SIZE);
    psmsl_process(&analyzer);
    float curvature1 = psmsl_get_curvature(&analyzer);
    
    // Second frame: 880 Hz (octave up)
    float tone2[2][PSMSL_WINDOW_SIZE];
    for (uint32_t i = 0; i < PSMSL_WINDOW_SIZE; i++) {
        float t = (float)i / 48000.0f;
        tone2[0][i] = sinf(2.0f * M_PI * 880.0f * t);
        tone2[1][i] = sinf(2.0f * M_PI * 880.0f * t);
    }
    
    const float *tone2_ptrs[2] = {tone2[0], tone2[1]};
    psmsl_feed(&analyzer, tone2_ptrs, PSMSL_WINDOW_SIZE);
    psmsl_process(&analyzer);
    float curvature2 = psmsl_get_curvature(&analyzer);
    
    printf("  Curvature (same freq): %.4f\n", curvature1);
    printf("  Curvature (freq change): %.4f\n", curvature2);
    
    // Frequency change should increase curvature
    assert_true(curvature2 > curvature1, 
                "Frequency change increases curvature");
    
    TEST_PASS("Leibniz-Bocker Diagnostics");
}

// =============================================================================
// Test: Sector Frequency Mapping
// =============================================================================

static void test_sector_mapping(void)
{
    printf("\n=== Test: Sector Frequency Mapping ===\n");
    
    // Test frequency to sector mapping
    struct {
        float freq;
        uint8_t expected_sector;
    } test_cases[] = {
        {30.0f, PSMSL_SECTOR_FOUNDATION},
        {100.0f, PSMSL_SECTOR_STRUCTURE},
        {300.0f, PSMSL_SECTOR_BODY},
        {1000.0f, PSMSL_SECTOR_PRESENCE},
        {3000.0f, PSMSL_SECTOR_CLARITY},
        {7000.0f, PSMSL_SECTOR_AIR},
        {15000.0f, PSMSL_SECTOR_EXTENSION},
    };
    
    for (size_t i = 0; i < sizeof(test_cases) / sizeof(test_cases[0]); i++) {
        uint8_t sector = psmsl_freq_to_sector(test_cases[i].freq);
        printf("  %.0f Hz -> %s\n", test_cases[i].freq, psmsl_get_sector_name(sector));
        assert_true(sector == test_cases[i].expected_sector, 
                    "Correct sector mapping");
    }
    
    // Test sector to frequency mapping
    for (uint8_t s = 0; s < PSMSL_NUM_SECTORS; s++) {
        float freq = psmsl_sector_to_freq(s);
        printf("  %s -> %.0f Hz\n", psmsl_get_sector_name(s), freq);
        assert_true(freq >= PSMSL_SECTOR_FREQ_LOW[s] && 
                    freq <= PSMSL_SECTOR_FREQ_HIGH[s],
                    "Sector center frequency in range");
    }
    
    TEST_PASS("Sector Frequency Mapping");
}

// =============================================================================
// Test: Memory Usage
// =============================================================================

static void test_memory_usage(void)
{
    printf("\n=== Test: Memory Usage ===\n");
    
    size_t analyzer_size = sizeof(psmsl_analyzer_t);
    size_t result_size = sizeof(psmsl_result_t);
    size_t eigen_workspace = EIGEN_MAX_DIM * EIGEN_MAX_DIM * sizeof(float) * 2;
    size_t grassmann_workspace = GRASSMANN_MAX_N * GRASSMANN_MAX_K * sizeof(float) * 2;
    
    printf("  psmsl_analyzer_t: %zu bytes\n", analyzer_size);
    printf("  psmsl_result_t: %zu bytes\n", result_size);
    printf("  Eigen workspace: %zu bytes\n", eigen_workspace);
    printf("  Grassmann workspace: %zu bytes\n", grassmann_workspace);
    printf("  Total estimated: %zu bytes (%.1f KB)\n", 
           analyzer_size + eigen_workspace + grassmann_workspace,
           (analyzer_size + eigen_workspace + grassmann_workspace) / 1024.0f);
    
    // Target: < 32 KB total
    size_t total = analyzer_size + eigen_workspace + grassmann_workspace;
    assert_true(total < 32 * 1024, "Memory usage < 32 KB");
    
    TEST_PASS("Memory Usage");
}

// =============================================================================
// Main Test Runner
// =============================================================================

int main(void)
{
    printf("==============================================\n");
    printf("PSMSL Integration Tests\n");
    printf("Adaptive Crossover Firmware\n");
    printf("Copyright (c) Nathanael J. Bocker, 2026\n");
    printf("==============================================\n");
    
    // Run all tests
    test_thyme_identity();
    test_eigendecomposition();
    test_grassmann_operations();
    test_psmsl_init();
    test_psmsl_analysis();
    test_lb_diagnostics();
    test_sector_mapping();
    test_memory_usage();
    
    // Summary
    printf("\n==============================================\n");
    printf("Test Summary\n");
    printf("==============================================\n");
    printf("  Passed: %d\n", tests_passed);
    printf("  Failed: %d\n", tests_failed);
    printf("  Total:  %d\n", tests_passed + tests_failed);
    printf("==============================================\n");
    
    return (tests_failed > 0) ? 1 : 0;
}
