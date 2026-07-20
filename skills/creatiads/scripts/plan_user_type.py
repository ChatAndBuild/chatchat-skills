#!/usr/bin/env python3
from build_mcp_task_plan import main as _main

if __name__ == "__main__":
    import sys
    if "--capability" not in sys.argv:
        sys.argv[1:1] = ["--capability", "user_type"]
    raise SystemExit(_main())
