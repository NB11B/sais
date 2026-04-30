/**
 * @file sais_integration.h
 * @brief SAIS Integration Shim for the Adaptive Engine (PSMSL Core)
 * 
 * This shim maps the Adaptive Engine's audio-centric terminology (e.g., "room modes")
 * to SAIS-specific use cases (e.g., "structural modes", "drone motor health").
 * It provides a unified API for the SAIS Controller Layer to initialize and query
 * the PSMSL (Phi-Scaled Mirrored Semantic Logic) engine.
 * 
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#ifndef SAIS_ADAPTIVE_INTEGRATION_H
#define SAIS_ADAPTIVE_INTEGRATION_H

#include <stdint.h>
#include <stdbool.h>
#include "psmsl_analysis.h"
#include "room_mode_detector_psmsl.h"
#include "spatial_decomposition_psmsl.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief SAIS Adaptive Engine Operational Modes
 */
typedef enum {
    SAIS_ADAPTIVE_MODE_STRUCTURAL_HEALTH,   // Vibration analysis (accelerometers)
    SAIS_ADAPTIVE_MODE_ACOUSTIC_ANOMALY,    // Spatial leak/fault detection (mic array)
    SAIS_ADAPTIVE_MODE_DRONE_HEALTH,        // Motor/propeller FFT analysis
    SAIS_ADAPTIVE_MODE_SPECTROMETRY         // Optical/Acoustic soil & crop analysis
} sais_adaptive_mode_t;

/**
 * @brief SAIS Adaptive Engine Configuration
 */
typedef struct {
    sais_adaptive_mode_t mode;
    uint32_t sample_rate_hz;
    uint16_t frame_size;
    uint8_t num_channels;
} sais_adaptive_config_t;

/**
 * @brief Initialize the SAIS Adaptive Engine
 * 
 * @param config Configuration parameters
 * @return true if successful
 */
bool sais_adaptive_init(const sais_adaptive_config_t *config);

/**
 * @brief Feed raw sensor data into the engine
 * 
 * @param data Pointer to raw sensor data (audio, vibration, or optical)
 * @param length Number of samples
 * @return true if a full frame was processed
 */
bool sais_adaptive_feed(const float *data, uint32_t length);

/**
 * @brief Get the current structural health status (Curvature/Stability)
 * 
 * Maps the Leibniz-Bocker diagnostic curvature to a structural stability metric.
 * 
 * @param out_stability Pointer to store stability metric (0.0 - 1.0)
 * @param out_anomaly_flag Pointer to store anomaly boolean
 * @return true if data is valid
 */
bool sais_adaptive_get_structural_health(float *out_stability, bool *out_anomaly_flag);

/**
 * @brief Get the direction of arrival for an acoustic anomaly
 * 
 * @param out_azimuth Pointer to store azimuth angle in degrees
 * @param out_confidence Pointer to store confidence metric (0.0 - 1.0)
 * @return true if a valid anomaly is detected
 */
bool sais_adaptive_get_anomaly_location(float *out_azimuth, float *out_confidence);

#ifdef __cplusplus
}
#endif

#endif // SAIS_ADAPTIVE_INTEGRATION_H
