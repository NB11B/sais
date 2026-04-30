/**
 * @file psmsl_grassmann.h
 * @brief Grassmann Manifold utilities for PSMSL analysis
 * 
 * Provides geometric operations on the Grassmann manifold Gr(k, N)
 * for tracking eigenspace evolution and computing curvature.
 * 
 * The Grassmann manifold is the space of all k-dimensional subspaces
 * of an N-dimensional vector space. We use it to track how the
 * principal subspace of the covariance matrix evolves over time.
 * 
 * Theoretical Foundation:
 * - Hermann Grassmann (1809-1877): Exterior algebra and Grassmannians
 * - Leibniz-Bocker Framework: Trajectories on Gr(k, N) as structural evolution
 * 
 * Adaptive Crossover Firmware
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef PSMSL_GRASSMANN_H
#define PSMSL_GRASSMANN_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// =============================================================================
// Configuration
// =============================================================================

#define GRASSMANN_MAX_N         32      // Maximum ambient dimension
#define GRASSMANN_MAX_K         8       // Maximum subspace dimension

// =============================================================================
// Grassmann Manifold Operations
// =============================================================================

/**
 * @brief Update subspace representation from eigenvectors
 * 
 * Extracts the top-k eigenvectors to form a subspace on Gr(k, N).
 * 
 * @param eigenvectors  Full eigenvector matrix (N x N)
 * @param subspace      Output subspace matrix (N x k)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void grassmann_update_subspace(const float eigenvectors[GRASSMANN_MAX_N][GRASSMANN_MAX_N],
                                float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                uint32_t n,
                                uint32_t k);

/**
 * @brief Compute geodesic distance between two subspaces
 * 
 * The geodesic distance on Gr(k, N) is the norm of the principal angles
 * between the two subspaces.
 * 
 * @param subspace1     First subspace (N x k)
 * @param subspace2     Second subspace (N x k)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 * @return              Geodesic distance
 */
float grassmann_distance(const float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                         const float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                         uint32_t n,
                         uint32_t k);

/**
 * @brief Compute principal angles between two subspaces
 * 
 * Principal angles θ₁ ≤ θ₂ ≤ ... ≤ θₖ characterize the relative
 * orientation of two k-dimensional subspaces.
 * 
 * @param subspace1     First subspace (N x k)
 * @param subspace2     Second subspace (N x k)
 * @param angles        Output principal angles (k)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void grassmann_principal_angles(const float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                 const float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                 float angles[GRASSMANN_MAX_K],
                                 uint32_t n,
                                 uint32_t k);

/**
 * @brief Compute curvature from subspace trajectory
 * 
 * Curvature (Ω) measures the rate of structural reorientation.
 * Computed as the geodesic distance divided by time step.
 * 
 * @param subspace_prev Previous subspace (N x k)
 * @param subspace_curr Current subspace (N x k)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 * @return              Curvature value (rad/frame)
 */
float grassmann_compute_curvature(const float subspace_prev[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                   const float subspace_curr[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                   uint32_t n,
                                   uint32_t k);

/**
 * @brief Compute tangent vector at current point
 * 
 * The tangent vector represents the instantaneous direction of
 * motion on the Grassmann manifold.
 * 
 * @param subspace_prev Previous subspace (N x k)
 * @param subspace_curr Current subspace (N x k)
 * @param tangent       Output tangent vector (N x k)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void grassmann_tangent(const float subspace_prev[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        const float subspace_curr[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float tangent[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        uint32_t n,
                        uint32_t k);

/**
 * @brief Project point onto Grassmann manifold
 * 
 * Ensures the subspace representation is orthonormal (valid point on Gr(k, N)).
 * Uses QR decomposition.
 * 
 * @param subspace      Subspace to project (N x k), modified in place
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void grassmann_project(float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        uint32_t n,
                        uint32_t k);

/**
 * @brief Exponential map on Grassmann manifold
 * 
 * Moves from current point along tangent direction by specified distance.
 * 
 * @param subspace      Current subspace (N x k)
 * @param tangent       Tangent direction (N x k)
 * @param result        Output subspace (N x k)
 * @param distance      Distance to move
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void grassmann_exp_map(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        const float tangent[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float result[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float distance,
                        uint32_t n,
                        uint32_t k);

/**
 * @brief Logarithmic map on Grassmann manifold
 * 
 * Computes the tangent vector that would take us from subspace1 to subspace2.
 * 
 * @param subspace1     Starting subspace (N x k)
 * @param subspace2     Target subspace (N x k)
 * @param tangent       Output tangent vector (N x k)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void grassmann_log_map(const float subspace1[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        const float subspace2[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        float tangent[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                        uint32_t n,
                        uint32_t k);

// =============================================================================
// Subspace Utilities
// =============================================================================

/**
 * @brief Compute projection matrix for subspace
 * 
 * P = U * U^T where U is the orthonormal basis
 * 
 * @param subspace      Subspace basis (N x k)
 * @param projection    Output projection matrix (N x N)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void subspace_projection_matrix(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                                 float projection[GRASSMANN_MAX_N][GRASSMANN_MAX_N],
                                 uint32_t n,
                                 uint32_t k);

/**
 * @brief Project vector onto subspace
 * 
 * @param subspace      Subspace basis (N x k)
 * @param vector        Input vector (N)
 * @param result        Output projected vector (N)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 */
void subspace_project_vector(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                              const float vector[GRASSMANN_MAX_N],
                              float result[GRASSMANN_MAX_N],
                              uint32_t n,
                              uint32_t k);

/**
 * @brief Compute residual (component orthogonal to subspace)
 * 
 * @param subspace      Subspace basis (N x k)
 * @param vector        Input vector (N)
 * @param residual      Output residual vector (N)
 * @param n             Ambient dimension N
 * @param k             Subspace dimension k
 * @return              Residual norm
 */
float subspace_residual(const float subspace[GRASSMANN_MAX_N][GRASSMANN_MAX_K],
                         const float vector[GRASSMANN_MAX_N],
                         float residual[GRASSMANN_MAX_N],
                         uint32_t n,
                         uint32_t k);

#ifdef __cplusplus
}
#endif

#endif // PSMSL_GRASSMANN_H
