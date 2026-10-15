"""InsightMesh command line."""
import argparse
import json
from pathlib import Path

from . import __version__
from .api import create_app
from .evidence import digest, verify
from .profiling import profile
from .storage import Store


def main():
    parser = argparse.ArgumentParser(prog="insightmesh", description="OREiLO InsightMesh")
    parser.add_argument("--database", default="./insightmesh.db")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("about")
    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8000)
    project = sub.add_parser("project-create")
    project.add_argument("name")
    project.add_argument("--description", default="")
    sub.add_parser("projects")
    dataset = sub.add_parser("profile")
    dataset.add_argument("file")
    fingerprint = sub.add_parser("hash")
    fingerprint.add_argument("file")
    check = sub.add_parser("verify")
    check.add_argument("file")
    check.add_argument("sha256")
    args = parser.parse_args()
    if args.command == "about":
        print(f"OREiLO InsightMesh v{__version__} | https://oreilo.com")
    elif args.command == "serve":
        import uvicorn
        import os
        os.environ["INSIGHTMESH_DB"] = args.database
        uvicorn.run(create_app(Store(args.database)), host=args.host, port=args.port)
    elif args.command == "project-create":
        print(json.dumps(Store(args.database).create_project(args.name, args.description), indent=2))
    elif args.command == "projects":
        print(json.dumps(Store(args.database).list_projects(), indent=2))
    elif args.command == "profile":
        file = Path(args.file)
        print(json.dumps(profile(file.name, file.read_text(encoding="utf-8-sig")), indent=2))
    elif args.command == "hash":
        print(digest(Path(args.file).read_text(encoding="utf-8")))
    elif args.command == "verify":
        print("VERIFIED" if verify(Path(args.file).read_text(encoding="utf-8"), args.sha256)
              else "MISMATCH")


if __name__ == "__main__":
    main()
