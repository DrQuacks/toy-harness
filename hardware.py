import platform
import subprocess


def get_hardware_profile() -> str:
    machine = platform.machine().lower()

    # Apple Silicon: arm64
    if machine == "arm64":
        return "apple_silicon"

    # Intel Mac: x86_64
    if machine == "x86_64":
        return "intel_mac"

    return "unknown"


def get_default_models() -> dict[str, str]:
    profile = get_hardware_profile()

    if profile == "apple_silicon":
        return {
            "router_model": "qwen2.5:0.5b",
            "coder_model": "qwen2.5-coder:7b",
        }

    if profile == "intel_mac":
        return {
            "router_model": "qwen2.5:0.5b",
            "coder_model": "qwen2.5-coder:3b",
        }

    return {
        "router_model": "qwen2.5:0.5b",
        "coder_model": "qwen2.5-coder:1.5b",
    }