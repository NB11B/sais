/**
 * @file psmsl_eigen.h
 * @brief Eigendecomposition utilities for PSMSL analysis
 * 
 * Provides efficient eigenvalue/eigenvector computation for symmetric
 * covariance matrices. Optimized for MCU with limited resources.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef PSMSL_EIGEN_H
#define PSMSL_EIGEN_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

#define EIGEN_MAX_DIM           32      // Maximum matrix dimension
#define EIGEN_MAX_ITERATIONS    100     // Maximum Jacobi iterations
#define EIGEN_TOLERANCE         1e-8f   // Convergence tolerance

// =============================================================================
// Eigendecomposition Functions
// =============================================================================

/**
 * @brief Compute eigendecomposition of symmetric matrix
 * 
 * Uses Jacobi rotation method, which is stable and suitable for
 * small-to-medium matrices on MCU. Eigenvalues are returned in
 * descending order.
 * 
 * @param matrix        Input symmetric matrix (n x n), will be modified
 * @param eigenvalues   Output eigenvalues (n), descending order
 * @param eigenvectors  Output eigenvectors (n x n), columns are vectors
 * @param n             Matrix dimension
 * @return              Number of iterations used, or -1 on failure
 */
int eigen_decompose(float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                    float eigenvalues[EIGEN_MAX_DIM],
                    float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                    uint32_t n);

/**
 * @brief Compute eigendecomposition with pre-allocated workspace
 * 
 * Same as eigen_decompose but allows external workspace allocation
 * to avoid stack usage.
 * 
 * @param matrix        Input symmetric matrix (n x n)
 * @param eigenvalues   Output eigenvalues (n)
 * @param eigenvectors  Output eigenvectors (n x n)
 * @param n             Matrix dimension
 * @param workspace     Workspace buffer (at least n * n floats)
 * @return              Number of iterations used, or -1 on failure
 */
int eigen_decompose_ext(const float *matrix,
                        float *eigenvalues,
                        float *eigenvectors,
                        uint32_t n,
                        float *workspace);

/**
 * @brief Compute only top-k eigenvalues/eigenvectors
 * 
 * Uses power iteration with deflation. More efficient when only
 * a few eigenvalues are needed.
 * 
 * @param matrix        Input symmetric matrix (n x n)
 * @param eigenvalues   Output top-k eigenvalues
 * @param eigenvectors  Output top-k eigenvectors (n x k)
 * @param n             Matrix dimension
 * @param k             Number of eigenvalues to compute
 * @return              true on success
 */
bool eigen_top_k(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                 float eigenvalues[EIGEN_MAX_DIM],
                 float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                 uint32_t n,
                 uint32_t k);

// =============================================================================
// Matrix Utilities
// =============================================================================

/**
 * @brief Compute matrix trace (sum of diagonal)
 * 
 * @param matrix        Input matrix
 * @param n             Matrix dimension
 * @return              Trace value
 */
float matrix_trace(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                   uint32_t n);

/**
 * @brief Compute Frobenius norm
 * 
 * @param matrix        Input matrix
 * @param n             Matrix dimension
 * @return              Frobenius norm
 */
float matrix_frobenius_norm(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                            uint32_t n);

/**
 * @brief Compute matrix-vector product
 * 
 * @param matrix        Input matrix (n x n)
 * @param vector        Input vector (n)
 * @param result        Output vector (n)
 * @param n             Dimension
 */
void matrix_vector_mult(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                        const float vector[EIGEN_MAX_DIM],
                        float result[EIGEN_MAX_DIM],
                        uint32_t n);

/**
 * @brief Normalize vector to unit length
 * 
 * @param vector        Vector to normalize (in-place)
 * @param n             Dimension
 * @return              Original norm
 */
float vector_normalize(float vector[EIGEN_MAX_DIM], uint32_t n);

/**
 * @brief Compute vector dot product
 * 
 * @param a             First vector
 * @param b             Second vector
 * @param n             Dimension
 * @return              Dot product
 */
float vector_dot(const float a[EIGEN_MAX_DIM],
                 const float b[EIGEN_MAX_DIM],
                 uint32_t n);

#ifdef __cplusplus
}
#endif

#endif // PSMSL_EIGEN_H
