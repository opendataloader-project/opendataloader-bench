from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


YYMMDD_PATTERN = re.compile(r"^\d{6}$")
EVALUATION_FILES = ("evaluation.json", "evaluation.csv")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy prediction/{engine}/evaluation.{json,csv} into "
            "history/{yymmdd}/{engine}/ to keep an archive."
        )
    )
    parser.add_argument(
        "--engine",
        help="Engine name (directory under prediction/ and history/). If omitted, every engine is archived.",
    )
    parser.add_argument(
        "--date",
        help="Target history folder in yymmdd format. Defaults to today's date.",
    )
    parser.add_argument(
        "--prediction-root",
        default="prediction",
        help="Path to the prediction root directory. Defaults to ./prediction",
    )
    parser.add_argument(
        "--history-root",
        default="history",
        help="Path to the history root directory. Defaults to ./history",
    )
    parser.add_argument(
        "--no-overwrite",
        dest="overwrite",
        default=True,
        action="store_false",
        help="Prevent overwriting existing history evaluation files. Overwrites are enabled by default.",
    )
    return parser.parse_args()


def _resolve_date(date_arg: str | None) -> str:
    if date_arg is None:
        return datetime.now().strftime("%y%m%d")
    if not YYMMDD_PATTERN.match(date_arg):
        raise ValueError("date must be 6 digits in yymmdd format")
    return date_arg


def archive_evaluation(
    engine: str,
    prediction_root: Path,
    history_root: Path,
    date_folder: str,
    overwrite: bool = False,
) -> Path:
    engine_prediction_dir = prediction_root / engine
    sources = {name: engine_prediction_dir / name for name in EVALUATION_FILES}
    missing = [str(path) for path in sources.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing prediction file(s): {', '.join(missing)}")

    destination_dir = history_root / date_folder / engine
    destination_dir.mkdir(parents=True, exist_ok=True)
    destinations = {name: destination_dir / name for name in EVALUATION_FILES}

    conflicts = [str(path) for path in destinations.values() if path.exists()]
    if conflicts and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {', '.join(conflicts)}. "
            "Run with --overwrite to replace it."
        )

    for name in EVALUATION_FILES:
        shutil.copy2(sources[name], destinations[name])
    return destination_dir


def _list_engines(prediction_root: Path) -> list[str]:
    if not prediction_root.exists():
        return []
    engines = [
        entry.name
        for entry in prediction_root.iterdir()
        if entry.is_dir() and (entry / "evaluation.json").exists()
    ]
    return sorted(engines)


def main() -> int:
    args = _parse_args()
    try:
        date_folder = _resolve_date(args.date)
        prediction_root = Path(args.prediction_root)
        history_root = Path(args.history_root)

        engines = [args.engine] if args.engine else _list_engines(prediction_root)
        if not engines:
            raise ValueError(
                "No engines found. Provide an engine or ensure prediction/*/evaluation.json exists."
            )

        copied: list[tuple[str, Path]] = []
        errors: list[tuple[str, Exception]] = []
        for engine in engines:
            try:
                destination = archive_evaluation(
                    engine=engine,
                    prediction_root=prediction_root,
                    history_root=history_root,
                    date_folder=date_folder,
                    overwrite=args.overwrite,
                )
            except Exception as exc:
                errors.append((engine, exc))
            else:
                copied.append((engine, destination))
    except Exception as exc:  # surface validation errors
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for engine, destination in copied:
        print(f"[{engine}] Archived evaluation files to {destination}")

    if errors:
        for engine, exc in errors:
            print(f"[{engine}] error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
