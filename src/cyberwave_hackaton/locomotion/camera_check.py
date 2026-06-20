"""Inspect and read the UGV Beast camera without sending locomotion commands."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from cyberwave import Cyberwave, CyberwaveError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = PROJECT_ROOT / "ugv_camera_latest.jpg"


def load_local_env() -> None:
    """Load project .env values without overriding variables exported by the shell."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def resolve_source_type(mode: str, requested_source_type: str | None) -> str:
    """Map the runtime mode to the latest-frame source expected by the REST API."""
    if requested_source_type:
        return requested_source_type
    return "sim" if mode == "simulation" else "tele"


def create_client(args: argparse.Namespace, source_type: str) -> Cyberwave:
    return Cyberwave(
        api_key=args.api_key,
        base_url=args.base_url,
        environment_id=args.environment_id,
        workspace_id=args.workspace_id,
        mode=args.mode,
        source_type=source_type,
    )


def get_existing_twin(client: Cyberwave, args: argparse.Namespace) -> Any:
    """Fetch an existing twin only; do not create one implicitly."""
    if not args.twin_id:
        raise CyberwaveError(
            "Missing twin id. Set CYBERWAVE_TWIN_UUID or pass --twin-id."
        )
    return client.twin(twin_id=args.twin_id)


def camera_sensors(twin: Any) -> list[dict[str, Any]]:
    sensors = twin.capabilities.get("sensors", [])
    if not isinstance(sensors, list):
        return []
    return [sensor for sensor in sensors if isinstance(sensor, dict)]


def default_sensor_id(twin: Any) -> str | None:
    sensors = camera_sensors(twin)
    if not sensors:
        return None
    sensor_id = sensors[0].get("id")
    return str(sensor_id) if sensor_id is not None else None


def print_twin_camera_summary(
    client: Cyberwave,
    twin: Any,
    sensor_id: str | None,
    source_type: str,
) -> None:
    print("Cyberwave camera check")
    print(f"mode: {client.config.runtime_mode}")
    print(f"frame_source_type: {source_type}")
    print(f"environment_id: {client.config.environment_id or 'not set'}")
    print(f"twin_uuid: {twin.uuid}")
    print(f"twin_name: {twin.name}")
    print(f"twin_class: {type(twin).__name__}")
    print(f"selected_sensor_id: {sensor_id or 'not set'}")
    print(f"has_start_streaming: {hasattr(twin, 'start_streaming')}")

    sensors = camera_sensors(twin)
    if not sensors:
        print("sensors: none")
        return

    print("sensors:")
    for sensor in sensors:
        params = sensor.get("parameters") or {}
        width = params.get("width", "?")
        height = params.get("height", "?")
        rate = params.get("update_rate", "?")
        print(
            "  "
            f"id={sensor.get('id', 'unknown')} "
            f"name={sensor.get('name', 'unknown')} "
            f"type={sensor.get('type', 'unknown')} "
            f"size={width}x{height} "
            f"rate={rate}Hz"
        )


def write_frame(output: Path, frame_bytes: bytes) -> None:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(frame_bytes)
    print(f"saved_frame: {output}")


def capture_cloud_latest(
    twin: Any,
    sensor_id: str | None,
    source_type: str,
    output: Path,
) -> None:
    # REST GET: reads the latest frame already uploaded to Cyberwave.
    # This does not publish a movement command to the robot.
    frame_bytes = twin.get_latest_frame(
        sensor_id=sensor_id,
        source_type=source_type,
    )
    write_frame(output, frame_bytes)


def capture_edge_photo(twin: Any, output: Path, timeout: float) -> None:
    # MQTT command: asks the edge device for a fresh photo.
    # It is not a locomotion command, but it does send `take_photo` to the robot edge.
    frame_bytes = twin.camera.edge_photo(format="bytes", timeout=timeout)
    write_frame(output, frame_bytes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect/read the UGV Beast camera without locomotion commands."
    )
    parser.add_argument("--api-key", default=os.getenv("CYBERWAVE_API_KEY"))
    parser.add_argument("--base-url", default=os.getenv("CYBERWAVE_BASE_URL"))
    parser.add_argument(
        "--environment-id",
        default=os.getenv("CYBERWAVE_ENVIRONMENT_ID"),
        help="Cyberwave environment UUID or slug.",
    )
    parser.add_argument(
        "--workspace-id",
        default=os.getenv("CYBERWAVE_WORKSPACE_ID"),
        help="Cyberwave workspace UUID.",
    )
    parser.add_argument(
        "--twin-id",
        default=os.getenv("CYBERWAVE_TWIN_UUID"),
        help="Existing UGV twin UUID or slug.",
    )
    parser.add_argument(
        "--mode",
        choices=("live", "simulation"),
        default=os.getenv("CYBERWAVE_CAMERA_MODE", "live"),
        help="Use live for the real UGV camera, simulation for simulator frames.",
    )
    parser.add_argument(
        "--source-type",
        choices=("tele", "sim"),
        default=os.getenv("CYBERWAVE_CAMERA_SOURCE_TYPE"),
        help="Latest-frame source. Defaults to tele in live mode and sim in simulation.",
    )
    parser.add_argument(
        "--sensor-id",
        default=os.getenv("UGV_BEAST_CAMERA_SENSOR_ID"),
        help="Camera sensor id. UGV Beast usually uses 'default'.",
    )
    parser.add_argument(
        "--capture",
        choices=("none", "cloud-latest", "edge-photo"),
        default="none",
        help=(
            "none only prints metadata; cloud-latest reads REST latest-frame; "
            "edge-photo sends take_photo to the edge device."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JPEG path used when --capture is enabled.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for --capture edge-photo.",
    )
    return parser


def main() -> int:
    load_local_env()
    parser = build_parser()
    args = parser.parse_args()

    source_type = resolve_source_type(args.mode, args.source_type)
    client = create_client(args, source_type)

    try:
        twin = get_existing_twin(client, args)
        sensor_id = args.sensor_id or default_sensor_id(twin)
        print_twin_camera_summary(client, twin, sensor_id, source_type)

        if args.capture == "cloud-latest":
            capture_cloud_latest(twin, sensor_id, source_type, args.output)
        elif args.capture == "edge-photo":
            if args.mode != "live":
                raise CyberwaveError("--capture edge-photo is only valid with --mode live.")
            capture_edge_photo(twin, args.output, args.timeout)
    except CyberwaveError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")
    finally:
        client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
