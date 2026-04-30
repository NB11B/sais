/**
 * @file sais_integration.c
 * @brief SAIS Integration Shim for the Adaptive Engine (PSMSL Core)
 * 
 * Implements the mapping between the Adaptive Engine's core PSMSL algorithms
 * and the SAIS Sovereign Node's operational requirements.
 * 
 * Copyright (c) Nathanael J. Bocker, 2026 all rights reserved
 */

#include "sais_integration.h"
#include <stddef.h>
#include <string.h>

// Internal state
static sais_adaptive_config_t current_config;
static spatial_psmsl_analyzer_t *spatial_analyzer = NULL;
static room_mode_detector_t *mode_detector = NULL;

bool sais_adaptive_init(const sais_adaptive_config_t *config) {
    if (!config) return false;
    
    memcpy(&current_config, config, sizeof(sais_adaptive_config_t));
    
    // Initialize the underlying PSMSL analysis engine
    if (!psmsl_analysis_init(config->sample_rate_hz, config->frame_size)) {
        return false;
    }
    
    // Initialize specific modules based on the SAIS mode
    switch (config->mode) {
        case SAIS_ADAPTIVE_MODE_STRUCTURAL_HEALTH:
        case SAIS_ADAPTIVE_MODE_DRONE_HEALTH:
            // These modes rely on the room_mode_detector (resonance tracking)
            mode_detector = room_mode_detector_create(config->sample_rate_hz, config->frame_size);
            if (!mode_detector) return false;
            break;
            
        case SAIS_ADAPTIVE_MODE_ACOUSTIC_ANOMALY:
            // This mode relies on spatial decomposition (mic array)
            spatial_analyzer = spatial_psmsl_create(config->sample_rate_hz, config->frame_size, config->num_channels);
            if (!spatial_analyzer) return false;
            break;
            
        case SAIS_ADAPTIVE_MODE_SPECTROMETRY:
            // Spectrometry relies directly on the base PSMSL FFT pipeline
            break;
            
        default:
            return false;
    }
    
    return true;
}

bool sais_adaptive_feed(const float *data, uint32_t length) {
    if (!data || length == 0) return false;
    
    // Feed data into the appropriate underlying module
    if (spatial_analyzer) {
        return spatial_psmsl_feed(spatial_analyzer, data, length);
    } else if (mode_detector) {
        // The mode detector expects a single channel of data (e.g., one accelerometer axis)
        return room_mode_detector_feed(mode_detector, data, length);
    }
    
    return false;
}

bool sais_adaptive_get_structural_health(float *out_stability, bool *out_anomaly_flag) {
    if (!out_stability || !out_anomaly_flag) return false;
    
    // In the PSMSL framework, structural stability is derived from the Grassmann curvature (Ω).
    // A high curvature indicates rapid, unstable changes in the resonant modes (e.g., a crack forming).
    // We map the Leibniz-Bocker diagnostic stability metric directly to SAIS structural health.
    
    if (spatial_analyzer) {
        *out_stability = spatial_psmsl_get_stability(spatial_analyzer);
        
        // Flag an anomaly if stability drops below 0.8 (configurable threshold)
        *out_anomaly_flag = (*out_stability < 0.8f);
        return true;
    }
    
    return false;
}

bool sais_adaptive_get_anomaly_location(float *out_azimuth, float *out_confidence) {
    if (!out_azimuth || !out_confidence || !spatial_analyzer) return false;
    
    spatial_doa_estimate_t doa;
    if (spatial_psmsl_estimate_doa(spatial_analyzer, &doa)) {
        *out_azimuth = doa.azimuth_deg;
        *out_confidence = doa.confidence;
        return true;
    }
    
    return false;
}
