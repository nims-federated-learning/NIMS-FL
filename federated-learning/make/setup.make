GEN_FILES += $(wildcard federated-learning_v*.run) geckodriver.log

PYTHON_VERSIONS := py38
# CUDA_BACKENDS := cpu

RELEASE_BUNDLE := dist/federated-learning_v$(PROJECT_VERSION).run