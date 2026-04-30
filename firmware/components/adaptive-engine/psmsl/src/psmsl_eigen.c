/**
 * @file psmsl_eigen.c
 * @brief Eigendecomposition utilities implementation
 * 
 * Jacobi rotation method for symmetric matrix eigendecomposition.
 * Optimized for MCU with single-precision floating point.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "psmsl_eigen.h"
#include <string.h>
#include <math.h>

// =============================================================================
// Private Helper Functions
// =============================================================================

/**
 * @brief Find the largest off-diagonal element
 */
static void find_max_offdiag(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                              uint32_t n,
                              uint32_t *p,
                              uint32_t *q,
                              float *max_val)
{
    *max_val = 0.0f;
    *p = 0;
    *q = 1;
    
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = i + 1; j < n; j++) {
            float val = fabsf(matrix[i][j]);
            if (val > *max_val) {
                *max_val = val;
                *p = i;
                *q = j;
            }
        }
    }
}

/**
 * @brief Apply Jacobi rotation to zero out element (p,q)
 */
static void jacobi_rotate(float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                          float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                          uint32_t n,
                          uint32_t p,
                          uint32_t q)
{
    float app = matrix[p][p];
    float aqq = matrix[q][q];
    float apq = matrix[p][q];
    
    // Compute rotation angle
    float theta;
    if (fabsf(app - aqq) < 1e-10f) {
        theta = (apq >= 0) ? 0.25f * 3.14159265f : -0.25f * 3.14159265f;
    } else {
        theta = 0.5f * atanf(2.0f * apq / (app - aqq));
    }
    
    float c = cosf(theta);
    float s = sinf(theta);
    
    // Update matrix elements
    matrix[p][p] = c * c * app + s * s * aqq - 2.0f * s * c * apq;
    matrix[q][q] = s * s * app + c * c * aqq + 2.0f * s * c * apq;
    matrix[p][q] = 0.0f;
    matrix[q][p] = 0.0f;
    
    // Update other elements
    for (uint32_t i = 0; i < n; i++) {
        if (i != p && i != q) {
            float aip = matrix[i][p];
            float aiq = matrix[i][q];
            matrix[i][p] = c * aip - s * aiq;
            matrix[p][i] = matrix[i][p];
            matrix[i][q] = s * aip + c * aiq;
            matrix[q][i] = matrix[i][q];
        }
    }
    
    // Update eigenvectors
    for (uint32_t i = 0; i < n; i++) {
        float vip = eigenvectors[i][p];
        float viq = eigenvectors[i][q];
        eigenvectors[i][p] = c * vip - s * viq;
        eigenvectors[i][q] = s * vip + c * viq;
    }
}

/**
 * @brief Sort eigenvalues and eigenvectors in descending order
 */
static void sort_eigen(float eigenvalues[EIGEN_MAX_DIM],
                       float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                       uint32_t n)
{
    // Simple selection sort (n is small)
    for (uint32_t i = 0; i < n - 1; i++) {
        uint32_t max_idx = i;
        for (uint32_t j = i + 1; j < n; j++) {
            if (eigenvalues[j] > eigenvalues[max_idx]) {
                max_idx = j;
            }
        }
        
        if (max_idx != i) {
            // Swap eigenvalues
            float temp = eigenvalues[i];
            eigenvalues[i] = eigenvalues[max_idx];
            eigenvalues[max_idx] = temp;
            
            // Swap eigenvector columns
            for (uint32_t k = 0; k < n; k++) {
                temp = eigenvectors[k][i];
                eigenvectors[k][i] = eigenvectors[k][max_idx];
                eigenvectors[k][max_idx] = temp;
            }
        }
    }
}

// =============================================================================
// Public API: Eigendecomposition
// =============================================================================

int eigen_decompose(float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                    float eigenvalues[EIGEN_MAX_DIM],
                    float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                    uint32_t n)
{
    if (n == 0 || n > EIGEN_MAX_DIM) {
        return -1;
    }
    
    // Initialize eigenvectors to identity
    memset(eigenvectors, 0, sizeof(float) * EIGEN_MAX_DIM * EIGEN_MAX_DIM);
    for (uint32_t i = 0; i < n; i++) {
        eigenvectors[i][i] = 1.0f;
    }
    
    // Jacobi iteration
    int iterations = 0;
    for (iterations = 0; iterations < EIGEN_MAX_ITERATIONS; iterations++) {
        uint32_t p, q;
        float max_val;
        find_max_offdiag(matrix, n, &p, &q, &max_val);
        
        if (max_val < EIGEN_TOLERANCE) {
            break;  // Converged
        }
        
        jacobi_rotate(matrix, eigenvectors, n, p, q);
    }
    
    // Extract eigenvalues from diagonal
    for (uint32_t i = 0; i < n; i++) {
        eigenvalues[i] = matrix[i][i];
    }
    
    // Sort in descending order
    sort_eigen(eigenvalues, eigenvectors, n);
    
    return iterations;
}

int eigen_decompose_ext(const float *matrix,
                        float *eigenvalues,
                        float *eigenvectors,
                        uint32_t n,
                        float *workspace)
{
    if (n == 0 || n > EIGEN_MAX_DIM || !workspace) {
        return -1;
    }
    
    // Copy matrix to workspace
    float (*work_matrix)[EIGEN_MAX_DIM] = (float (*)[EIGEN_MAX_DIM])workspace;
    float (*work_eigen)[EIGEN_MAX_DIM] = (float (*)[EIGEN_MAX_DIM])(workspace + n * n);
    
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            work_matrix[i][j] = matrix[i * n + j];
        }
    }
    
    // Initialize eigenvectors
    memset(work_eigen, 0, sizeof(float) * n * n);
    for (uint32_t i = 0; i < n; i++) {
        work_eigen[i][i] = 1.0f;
    }
    
    // Jacobi iteration
    int iterations = 0;
    for (iterations = 0; iterations < EIGEN_MAX_ITERATIONS; iterations++) {
        uint32_t p, q;
        float max_val;
        find_max_offdiag(work_matrix, n, &p, &q, &max_val);
        
        if (max_val < EIGEN_TOLERANCE) {
            break;
        }
        
        jacobi_rotate(work_matrix, work_eigen, n, p, q);
    }
    
    // Copy results
    for (uint32_t i = 0; i < n; i++) {
        eigenvalues[i] = work_matrix[i][i];
        for (uint32_t j = 0; j < n; j++) {
            eigenvectors[i * n + j] = work_eigen[i][j];
        }
    }
    
    return iterations;
}

bool eigen_top_k(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                 float eigenvalues[EIGEN_MAX_DIM],
                 float eigenvectors[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                 uint32_t n,
                 uint32_t k)
{
    if (n == 0 || n > EIGEN_MAX_DIM || k == 0 || k > n) {
        return false;
    }
    
    // Copy matrix for deflation
    float work[EIGEN_MAX_DIM][EIGEN_MAX_DIM];
    memcpy(work, matrix, sizeof(work));
    
    // Power iteration with deflation
    for (uint32_t i = 0; i < k; i++) {
        // Initialize random vector
        float v[EIGEN_MAX_DIM];
        for (uint32_t j = 0; j < n; j++) {
            v[j] = 1.0f / sqrtf((float)n);
        }
        
        // Power iteration
        for (int iter = 0; iter < EIGEN_MAX_ITERATIONS; iter++) {
            float v_new[EIGEN_MAX_DIM];
            matrix_vector_mult(work, v, v_new, n);
            
            float norm = vector_normalize(v_new, n);
            
            // Check convergence
            float diff = 0.0f;
            for (uint32_t j = 0; j < n; j++) {
                diff += fabsf(v_new[j] - v[j]);
            }
            
            memcpy(v, v_new, sizeof(v));
            
            if (diff < EIGEN_TOLERANCE) {
                break;
            }
        }
        
        // Compute eigenvalue: λ = v^T A v
        float Av[EIGEN_MAX_DIM];
        matrix_vector_mult(work, v, Av, n);
        eigenvalues[i] = vector_dot(v, Av, n);
        
        // Store eigenvector
        for (uint32_t j = 0; j < n; j++) {
            eigenvectors[j][i] = v[j];
        }
        
        // Deflate: A = A - λ * v * v^T
        for (uint32_t j = 0; j < n; j++) {
            for (uint32_t l = 0; l < n; l++) {
                work[j][l] -= eigenvalues[i] * v[j] * v[l];
            }
        }
    }
    
    return true;
}

// =============================================================================
// Public API: Matrix Utilities
// =============================================================================

float matrix_trace(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                   uint32_t n)
{
    float trace = 0.0f;
    for (uint32_t i = 0; i < n; i++) {
        trace += matrix[i][i];
    }
    return trace;
}

float matrix_frobenius_norm(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                            uint32_t n)
{
    float sum = 0.0f;
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            sum += matrix[i][j] * matrix[i][j];
        }
    }
    return sqrtf(sum);
}

void matrix_vector_mult(const float matrix[EIGEN_MAX_DIM][EIGEN_MAX_DIM],
                        const float vector[EIGEN_MAX_DIM],
                        float result[EIGEN_MAX_DIM],
                        uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        result[i] = 0.0f;
        for (uint32_t j = 0; j < n; j++) {
            result[i] += matrix[i][j] * vector[j];
        }
    }
}

float vector_normalize(float vector[EIGEN_MAX_DIM], uint32_t n)
{
    float norm = 0.0f;
    for (uint32_t i = 0; i < n; i++) {
        norm += vector[i] * vector[i];
    }
    norm = sqrtf(norm);
    
    if (norm > 1e-10f) {
        for (uint32_t i = 0; i < n; i++) {
            vector[i] /= norm;
        }
    }
    
    return norm;
}

float vector_dot(const float a[EIGEN_MAX_DIM],
                 const float b[EIGEN_MAX_DIM],
                 uint32_t n)
{
    float dot = 0.0f;
    for (uint32_t i = 0; i < n; i++) {
        dot += a[i] * b[i];
    }
    return dot;
}
