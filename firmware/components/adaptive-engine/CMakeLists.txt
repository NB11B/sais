# SAIS Adaptive Engine Component
# Integrates the PSMSL (Phi-Scaled Mirrored Semantic Logic) core for
# structural health monitoring, acoustic anomaly detection, and spectrometry.

idf_component_register(
    SRCS "psmsl/src/psmsl_analysis.c"
         "psmsl/src/psmsl_diagnostics.c"
         "psmsl/src/psmsl_eigen.c"
         "psmsl/src/psmsl_grassmann.c"
         "psmsl/src/psmsl_serial_test.c"
         "core/src/adaptation_controller_psmsl.c"
         "core/src/room_mode_detector_psmsl.c"
         "core/src/spatial_decomposition_psmsl.c"
         "sais_integration.c"
    INCLUDE_DIRS "psmsl/include"
                 "core/include"
                 "."
    REQUIRES "esp_dsp" "driver"
)

# Enable PSMSL analysis by default for SAIS
target_compile_definitions(${COMPONENT_LIB} PUBLIC USE_PSMSL_ANALYSIS=1)
