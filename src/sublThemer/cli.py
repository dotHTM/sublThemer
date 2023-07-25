from __future__ import annotations

import json
import os
from pprint import pp
from tempfile import NamedTemporaryFile
from typing import Optional
from typing import Sequence

from .ColorScheme import ColorSchemeConfig


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filePath",
        type=str,
    )
    parser.add_argument(
        "filter",
        nargs="+",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
    )

    args = parser.parse_args(argv)

    # try:
    schemeData = ColorSchemeConfig.fromFile(args.filePath)
    # except Exception as e:
    #     print("ERROR:", str(e))
    #     return 1

    outputBuffer = json.dumps(schemeData.tags(args.filter), indent=2)

    if args.output:
        with NamedTemporaryFile("w", delete=False) as file:
            file.write(outputBuffer)
            os.replace(file.name, args.output)
    else:
        print(outputBuffer)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
