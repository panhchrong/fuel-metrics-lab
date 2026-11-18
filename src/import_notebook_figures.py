"""Export saved figures and tagged fuel-study results without executing notebook code."""
import argparse
import base64
import json
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "dashboard/public/study/notebook"
FORMATS = {"image/png": "png", "image/jpeg": "jpg", "image/svg+xml": "svg",
           "image/gif": "gif", "image/webp": "webp"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    gallery = {"sources": [], "figures": [], "unavailable": []}
    for book, path in enumerate(args.notebook, 1):
        gallery["sources"].append(path.name)
        heading = ""
        for cell, content in enumerate(json.loads(path.read_text())["cells"], 1):
            if content["cell_type"] == "markdown":
                for line in "".join(content["source"]).splitlines():
                    if line.startswith("#"):
                        heading = line.lstrip("# ").strip()
            for output, entry in enumerate(content.get("outputs", []), 1):
                data = entry.get("data", {})
                if ("fuel-study-results" in content.get("metadata", {}).get("tags", [])
                        and "application/json" in data):
                    gallery["study"] = data["application/json"]
                    continue
                meta = dict(source=path.name, cell=cell, output=output, title=heading or "Notebook output")
                mime = next((m for m in FORMATS if m in data), None)
                if mime:
                    file = f"book-{book}-cell-{cell}-output-{output}.{FORMATS[mime]}"
                    value = "".join(data[mime])
                    payload = value.encode() if mime == "image/svg+xml" else base64.b64decode(value)
                    (args.out / file).write_bytes(payload)
                    gallery["figures"].append(dict(**meta, file=file))
                elif data.keys() - {"text/plain"} or "<Figure " in "".join(data.get("text/plain", "")):
                    gallery["unavailable"].append(meta)
    (args.out / "gallery.json").write_text(json.dumps(gallery, indent=2))
    print(f"Imported {len(gallery['figures'])} figures. "
          f"{len(gallery['unavailable'])} rich outputs need a saved image representation.")


if __name__ == "__main__":
    main()
