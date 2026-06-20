"""CLI helpers for controlling the Waveshare UGV Beast through Cyberwave."""

from __future__ import annotations

import argparse
import os
from typing import Any, Callable

from cyberwave import Cyberwave, CyberwaveError


ASSET_KEY = "waveshare/ugv-beast"
DEFAULT_LINEAR_SPEED_M_S = 0.15
DEFAULT_ANGULAR_SPEED_RAD_S = 0.35
DEFAULT_DURATION_S = 0.5
DEFAULT_RATE_HZ = 10.0


def _camera_id(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _create_client(args: argparse.Namespace) -> Cyberwave:
    return Cyberwave(
        api_key=args.api_key,
        base_url=args.base_url,
        environment_id=args.environment_id,
        workspace_id=args.workspace_id,
        mode=args.mode,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
    )


def _get_ugv_twin(client: Cyberwave, args: argparse.Namespace) -> Any:
    if args.twin_id:
        return client.twin(twin_id=args.twin_id)
    return client.twin(ASSET_KEY, environment_id=args.environment_id)


def _print_twin_summary(twin: Any) -> None:
    capabilities = twin.capabilities
    sensors = capabilities.get("sensors", [])
    sensor_summary = ", ".join(
        f"{sensor.get('id', 'unknown')}:{sensor.get('type', 'unknown')}"
        for sensor in sensors
        if isinstance(sensor, dict)
    )

    print(f"name: {twin.name}")
    print(f"uuid: {twin.uuid}")
    print(f"class: {type(twin).__name__}")
    print(f"asset: {ASSET_KEY}")
    print(f"can_locomote: {bool(capabilities.get('can_locomote'))}")
    print(f"has_wheels: {bool(capabilities.get('has_wheels'))}")
    print(f"sensors: {sensor_summary or 'none'}")


def _connect(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    client.mqtt.connect()
    _print_twin_summary(twin)
    print(f"mqtt_connected: {client.mqtt.connected}")


def _status(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    _print_twin_summary(twin)


def _forward(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.move_forward(
        args.speed,
        duration=args.duration,
        rate_hz=args.rate_hz,
        source_type=args.source_type,
    )
    print(f"sent: forward speed={args.speed}m/s duration={args.duration}s")


def _backward(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.move_backward(
        args.speed,
        duration=args.duration,
        rate_hz=args.rate_hz,
        source_type=args.source_type,
    )
    print(f"sent: backward speed={args.speed}m/s duration={args.duration}s")


def _turn_left(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.turn_left(
        args.speed,
        duration=args.duration,
        rate_hz=args.rate_hz,
        source_type=args.source_type,
    )
    print(f"sent: turn-left speed={args.speed}rad/s duration={args.duration}s")


def _turn_right(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.turn_right(
        args.speed,
        duration=args.duration,
        rate_hz=args.rate_hz,
        source_type=args.source_type,
    )
    print(f"sent: turn-right speed={args.speed}rad/s duration={args.duration}s")


def _move(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.locomotion.move(
        linear_x=args.linear_x,
        angular_z=args.angular_z,
        duration=args.duration,
        rate_hz=args.rate_hz,
        source_type=args.source_type,
    )
    print(
        "sent: move "
        f"linear_x={args.linear_x}m/s angular_z={args.angular_z}rad/s "
        f"duration={args.duration}s"
    )


def _stop(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.locomotion.stop(source_type=args.source_type)
    print("sent: stop")


def _stream(args: argparse.Namespace, client: Cyberwave, twin: Any) -> None:
    twin.start_streaming(
        fps=args.fps,
        camera_id=args.camera_id,
        camera_name=args.camera_name,
    )


def _add_common_motion_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION_S,
        help="Command burst duration in seconds.",
    )
    parser.add_argument(
        "--rate-hz",
        type=float,
        default=DEFAULT_RATE_HZ,
        help="Publish rate while the command burst is active.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Control a Waveshare UGV Beast through the Cyberwave SDK."
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
        help="Existing UGV twin UUID or slug. If omitted, the SDK gets or creates one.",
    )
    parser.add_argument(
        "--mode",
        choices=("live", "simulation"),
        default=os.getenv("CYBERWAVE_MODE", "live"),
    )
    parser.add_argument("--mqtt-host", default=os.getenv("CYBERWAVE_MQTT_HOST"))
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=(
            int(os.environ["CYBERWAVE_MQTT_PORT"])
            if os.getenv("CYBERWAVE_MQTT_PORT")
            else None
        ),
    )
    parser.add_argument(
        "--source-type",
        choices=("tele", "sim_tele"),
        default=os.getenv("CYBERWAVE_SOURCE_TYPE"),
        help="Outbound command source. Defaults to tele in live mode and sim_tele in simulation.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    connect = subparsers.add_parser("connect", help="Create the SDK client and open MQTT.")
    connect.set_defaults(handler=_connect)

    status = subparsers.add_parser("status", help="Print the resolved twin metadata.")
    status.set_defaults(handler=_status)

    forward = subparsers.add_parser("forward", help="Drive forward at a linear speed.")
    forward.add_argument("--speed", type=float, default=DEFAULT_LINEAR_SPEED_M_S)
    _add_common_motion_args(forward)
    forward.set_defaults(handler=_forward)

    backward = subparsers.add_parser("backward", help="Drive backward at a linear speed.")
    backward.add_argument("--speed", type=float, default=DEFAULT_LINEAR_SPEED_M_S)
    _add_common_motion_args(backward)
    backward.set_defaults(handler=_backward)

    turn_left = subparsers.add_parser("turn-left", help="Turn left at an angular speed.")
    turn_left.add_argument("--speed", type=float, default=DEFAULT_ANGULAR_SPEED_RAD_S)
    _add_common_motion_args(turn_left)
    turn_left.set_defaults(handler=_turn_left)

    turn_right = subparsers.add_parser("turn-right", help="Turn right at an angular speed.")
    turn_right.add_argument("--speed", type=float, default=DEFAULT_ANGULAR_SPEED_RAD_S)
    _add_common_motion_args(turn_right)
    turn_right.set_defaults(handler=_turn_right)

    move = subparsers.add_parser("move", help="Publish a custom velocity command.")
    move.add_argument("--linear-x", type=float, default=0.0)
    move.add_argument("--angular-z", type=float, default=0.0)
    _add_common_motion_args(move)
    move.set_defaults(handler=_move)

    stop = subparsers.add_parser("stop", help="Publish an immediate stop command.")
    stop.set_defaults(handler=_stop)

    stream = subparsers.add_parser("stream", help="Start blocking camera streaming.")
    stream.add_argument("--fps", type=int, default=15)
    stream.add_argument(
        "--camera-id",
        type=_camera_id,
        default=_camera_id(os.getenv("UGV_BEAST_CAMERA_ID", "0")),
    )
    stream.add_argument("--camera-name", default=None)
    stream.set_defaults(handler=_stream)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    client = None
    try:
        client = _create_client(args)
        twin = _get_ugv_twin(client, args)
        handler: Callable[[argparse.Namespace, Cyberwave, Any], None] = args.handler
        handler(args, client, twin)
    except (CyberwaveError, ValueError) as exc:
        parser.exit(status=1, message=f"error: {exc}\n")
    finally:
        if client is not None:
            client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
