/**
 * @file psmsl_grassmann.c
 * @brief Grassmann Manifold utilities implementation
 * 
 * Geometric operations on Gr(k, N) for eigenspace trajectory tracking.
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "psmsl_grassmann.h"
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =============================================================================
// Private Helper Functions
// =============================================================================

/**
 * @brief Gram-Schmidt orthonormalization
 */
static void gram_schmidt(float matrix[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                          uint32_t n,
                          uint32_t k)
{
    for (uint32_t j = 0; j < k; j++) {
        // Subtract projections onto previous vectors
        for (uint32_t i = 0; i < j; i++) {
            float dot = 0.0f;
            for (uint32_t l = 0; l < n; l++) {
                dot += matrix[l][j] * matrix[l][i];
            }
            for (uint32_t l = 0; l < n; l++) {
                matrix[l][j] -= dot * matrix[l][i];
            }
        }
        
        // Normalize
        float norm = 0.0f;
        for (uint32_t l = 0; l < n; l++) {
            norm += matrix[l][j] * matrix[l][j];
        }
        norm = sqrtf(norm);
        
        if (norm > 1e-10f) {
            for (uint32_t l = 0; l < n; l++) {
                matrix[l][j] /= norm;
            }
        }
    }
}

/**
 * @brief Compute U1^T * U2 for principal angle computation
 */
static void compute_overlap_matrix(const float U1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                    const float U2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                    float overlap[GRASSMANN_MAX_K][GRASSMANN_MAX_K],
                                    uint32_t n,
                                    uint32_t k)
{
    for (uint32_t i = 0; i < k; i++) {
        for (uint32_t j = 0; j < k; j++) {
            overlap[i][j] = 0.0f;
            for (uint32_t l = 0; l < n; l++) {
                overlap[i][j] += U1[l][i] * U2[l][j];
            }
        }
    }
}

/**
 * @brief Compute singular values of small matrix (for principal angles)
 * Uses simple power iteration for small k
 */
static void compute_singular_values(const float matrix[GRASSMANN_MAX_K][GRASSMANN_MAX_K],
                                     float singular_values[GRASSMANN_MAX_K],
                                     uint32_t k)
{
    // Compute M^T * M
    float MtM[GRASSMANN_MAX_K][GRASSMANN_MAX_K];
    for (uint32_t i = 0; i < k; i++) {
        for (uint32_t j = 0; j < k; j++) {
            MtM[i][j] = 0.0f;
            for (uint32_t l = 0; l < k; l++) {
                MtM[i][j] += matrix[l][i] * matrix[l][j];
            }
        }
    }
    
    // Power iteration with deflation to get eigenvalues of M^T * M
    // (which are squares of singular values)
    for (uint32_t i = 0; i < k; i++) {
        float v[GRASSMANN_MAX_K];
        for (uint32_t j = 0; j < k; j++) {
            v[j] = 1.0f / sqrtf((float)k);
        }
        
        float eigenvalue = 0.0f;
        for (int iter = 0; iter < 50; iter++) {
            // v = MtM * v
            float v_new[GRASSMANN_MAX_K];
            for (uint32_t j = 0; j < k; j++) {
                v_new[j] = 0.0f;
                for (uint32_t l = 0; l < k; l++) {
                    v_new[j] += MtM[j][l] * v[l];
                }
            }
            
            // Normalize
            float norm = 0.0f;
            for (uint32_t j = 0; j < k; j++) {
                norm += v_new[j] * v_new[j];
            }
            norm = sqrtf(norm);
            
            if (norm < 1e-10f) break;
            
            eigenvalue = norm;
            for (uint32_t j = 0; j < k; j++) {
                v[j] = v_new[j] / norm;
            }
        }
        
        singular_values[i] = sqrtf(eigenvalue);
        
        // Deflate
        for (uint32_t j = 0; j < k; j++) {
            for (uint32_t l = 0; l < k; l++) {
                MtM[j][l] -= eigenvalue * v[j] * v[l];
            }
        }
    }
    
    // Sort descending
    for (uint32_t i = 0; i < k - 1; i++) {
        for (uint32_t j = i + 1; j < k; j++) {
            if (singular_values[j] > singular_values[i]) {
                float temp = singular_values[i];
                singular_values[i] = singular_values[j];
                singular_values[j] = temp;
            }
        }
    }
}

// =============================================================================
// Public API: Grassmann Manifold Operations
// =============================================================================

void grassmann_update_subspace(const float eigenvectors[GRASSMANN_MAX_N][GRASSMANN_MAX_N],
                                float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                uint32_t n,
                                uint32_t k)
{
    // Copy top-k eigenvectors (already sorted by eigenvalue)
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < k; j++) {
            subspace[i][j] = eigenvectors[i][j];
        }
    }
    
    // Ensure orthonormality
    gram_schmidt(subspace, n, k);
}

float grassmann_distance(const float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                         const float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                         uint32_t n,
                         uint32_t k)
{
    float angles[GRASSMANN_MAX_K];
    grassmann_principal_angles(subspace1, subspace2, angles, n, k);
    
    // Geodesic distance = sqrt(sum of squared principal angles)
    float dist_sq = 0.0f;
    for (uint32_t i = 0; i < k; i++) {
        dist_sq += angles[i] * angles[i];
    }
    
    return sqrtf(dist_sq);
}

void grassmann_principal_angles(const float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                 const float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                 float angles[GRASSMANN_MAX_K],
                                 uint32_t n,
                                 uint32_t k)
{
    // Compute overlap matrix U1^T * U2
    float overlap[GRASSMANN_MAX_K][GRASSMANN_MAX_K];
    compute_overlap_matrix(subspace1, subspace2, overlap, n, k);
    
    // Singular values of overlap matrix give cos(θ)
    float singular_values[GRASSMANN_MAX_K];
    compute_singular_values(overlap, singular_values, k);
    
    // Convert to angles
    for (uint32_t i = 0; i < k; i++) {
        // Clamp to valid range for acos
        float sv = singular_values[i];
        if (sv > 1.0f) sv = 1.0f;
        if (sv < -1.0f) sv = -1.0f;
        angles[i] = acosf(sv);
    }
}

float grassmann_compute_curvature(const float subspace_prev[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                   const float subspace_curr[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                   uint32_t n,
                                   uint32_t k)
{
    // Curvature = geodesic distance between consecutive subspaces
    // This is the discrete approximation to the geodesic curvature
    return grassmann_distance(subspace_prev, subspace_curr, n, k);
}

void grassmann_tangent(const float subspace_prev[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        const float subspace_curr[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float tangent[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        uint32_t n,
                        uint32_t k)
{
    // Simplified tangent: difference projected to tangent space
    // T = (I - U*U^T) * (U_curr - U_prev)
    
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < k; j++) {
            // Difference
            float diff = subspace_curr[i][j] - subspace_prev[i][j];
            
            // Project out component along current subspace
            float proj = 0.0f;
            for (uint32_t l = 0; l < k; l++) {
                float dot = 0.0f;
                for (uint32_t m = 0; m < n; m++) {
                    dot += subspace_prev[m][l] * (subspace_curr[m][j] - subspace_prev[m][j]);
                }
                proj += subspace_prev[i][l] * dot;
            }
            
            tangent[i][j] = diff - proj;
        }
    }
}

void grassmann_project(float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        uint32_t n,
                        uint32_t k)
{
    gram_schmidt(subspace, n, k);
}

void grassmann_exp_map(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        const float tangent[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float result[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float distance,
                        uint32_t n,
                        uint32_t k)
{
    // Simplified exponential map: move along tangent and reproject
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < k; j++) {
            result[i][j] = subspace[i][j] + distance * tangent[i][j];
        }
    }
    
    // Project back to manifold
    grassmann_project(result, n, k);
}

void grassmann_log_map(const float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        const float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float tangent[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        uint32_t n,
                        uint32_t k)
{
    // Log map is the inverse of exp map
    // For small distances, tangent ≈ U2 - U1 projected to tangent space
    grassmann_tangent(subspace1, subspace2, tangent, n, k);
}

// =============================================================================
// Public API: Subspace Utilities
// =============================================================================

void subspace_projection_matrix(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                 float projection[GRASSMANN_MAX_N][GRASSMANN_MAX_N],
                                 uint32_t n,
                                 uint32_t k)
{
    // P = U * U^T
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            projection[i][j] = 0.0f;
            for (uint32_t l = 0; l < k; l++) {
                projection[i][j] += subspace[i][l] * subspace[j][l];
            }
        }
    }
}

void subspace_project_vector(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                              const float vector[GRASSMANN_MAX_N],
                              float result[GRASSMANN_MAX_N],
                              uint32_t n,
                              uint32_t k)
{
    // result = U * U^T * v
    memset(result, 0, sizeof(float) * n);
    
    for (uint32_t j = 0; j < k; j++) {
        // Compute U^T * v for column j
        float dot = 0.0f;
        for (uint32_t i = 0; i < n; i++) {
            dot += subspace[i][j] * vector[i];
        }
        
        // Add contribution to result
        for (uint32_t i = 0; i < n; i++) {
            result[i] += subspace[i][j] * dot;
        }
    }
}

float subspace_residual(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                         const float vector[GRASSMANN_MAX_N],
                         float residual[GRASSMANN_MAX_N],
                         uint32_t n,
                         uint32_t k)
{
    // residual = v - P*v = (I - U*U^T)*v
    float projected[GRASSMANN_MAX_N];
    subspace_project_vector(subspace, vector, projected, n, k);
    
    float norm_sq = 0.0f;
    for (uint32_t i = 0; i < n; i++) {
        residual[i] = vector[i] - projected[i];
        norm_sq += residual[i] * residual[i];
    }
    
    return sqrtf(norm_sq);
}
