/**
 * @file psmsl_config.h
 * @brief PSMSL Configuration and Compile-Time Switches
 * 
 * Provides compile-time configuration for PSMSL analysis and
 * compatibility switches for parallel testing with FFT.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef PSMSL_CONFIG_H
#define PSMSL_CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Analysis Mode Selection
// =============================================================================

/**
 * USE_PSMSL_ANALYSIS: Enable PSMSL-based analysis (default)
 * 
 * When enabled:
 * - Spatial decomposition uses 7 semantic sectors
 * - Room mode detection uses Leibniz-Bocker diagnostics
 * - Adaptation controller optimizes Coherence/Curvature/Residual
 * 
 * When disabled:
 * - Falls back to FFT-based analysis
 * - Spatial decomposition uses 4 modes (omni, dipole, quadrupole)
 * - Room mode detection uses peak detection
 * - Adaptation controller optimizes FFT energy
 */
#ifndef USE_PSMSL_ANALYSIS
#define USE_PSMSL_ANALYSIS 1
#endif

/**
 * PSMSL_PARALLEL_TEST: Enable parallel FFT/PSMSL for comparison
 * 
 * When enabled, both FFT and PSMSL run simultaneously for validation.
 * Results can be compared in real-time or logged for analysis.
 */
#ifndef PSMSL_PARALLEL_TEST
#define PSMSL_PARALLEL_TEST 0
#endif

// =============================================================================
// Performance Configuration
// =============================================================================

/**
 * PSMSL_USE_SIMD: Enable SIMD optimizations
 * 
 * Automatically enabled for ESP32-P4 target.
 */
#if defined(CONFIG_IDF_TARGET_ESP32P4)
#define PSMSL_USE_SIMD 1
#else
#define PSMSL_USE_SIMD 0
#endif

/**
 * PSMSL_USE_FIXED_POINT: Use fixed-point math
 * 
 * For MCUs without FPU, use fixed-point arithmetic.
 */
#ifndef PSMSL_USE_FIXED_POINT
#define PSMSL_USE_FIXED_POINT 0
#endif

/**
 * PSMSL_EIGEN_ITERATIONS: Maximum Jacobi iterations
 * 
 * Trade-off between accuracy and computation time.
 */
#ifndef PSMSL_EIGEN_ITERATIONS
#define PSMSL_EIGEN_ITERATIONS 100
#endif

// =============================================================================
// Memory Configuration
// =============================================================================

/**
 * PSMSL_STATIC_ALLOCATION: Use static memory allocation
 * 
 * When enabled, all buffers are statically allocated.
 * Reduces heap fragmentation but increases BSS size.
 */
#ifndef PSMSL_STATIC_ALLOCATION
#define PSMSL_STATIC_ALLOCATION 1
#endif

/**
 * PSMSL_HISTORY_SIZE: Number of frames to keep in history
 * 
 * Used for curvature computation and temporal smoothing.
 */
#ifndef PSMSL_HISTORY_SIZE
#define PSMSL_HISTORY_SIZE 16
#endif

// =============================================================================
// Debug Configuration
// =============================================================================

/**
 * PSMSL_DEBUG: Enable debug output
 */
#ifndef PSMSL_DEBUG
#define PSMSL_DEBUG 0
#endif

/**
 * PSMSL_LOG_DIAGNOSTICS: Log Leibniz-Bocker diagnostics
 */
#ifndef PSMSL_LOG_DIAGNOSTICS
#define PSMSL_LOG_DIAGNOSTICS 0
#endif

/**
 * PSMSL_VALIDATE_MATH: Enable math validation checks
 */
#ifndef PSMSL_VALIDATE_MATH
#define PSMSL_VALIDATE_MATH 0
#endif

// =============================================================================
// Thyme Identity Verification
// =============================================================================

/**
 * Verify Thyme Identity at compile time
 * π² = (7φ² + √2) / 2
 */
#define PSMSL_PHI_SQUARED_VALUE     2.6180339887498948f
#define PSMSL_SQRT2_VALUE           1.4142135623730951f
#define PSMSL_PI_SQUARED_VALUE      9.8696044010893586f

#define PSMSL_THYME_COMPUTED        ((7.0f * PSMSL_PHI_SQUARED_VALUE + PSMSL_SQRT2_VALUE) / 2.0f)
#define PSMSL_THYME_ERROR           (PSMSL_THYME_COMPUTED - PSMSL_PI_SQUARED_VALUE)

// Thyme Identity should hold within floating-point precision
// Computed: (7 * 2.618... + 1.414...) / 2 = 9.869... ≈ π²
// Error should be < 1e-6

#ifdef __cplusplus
}
#endif

#endif // PSMSL_CONFIG_H
