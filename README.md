# packaide-irregular-stock-pod-serverless

RunPod serverless worker for packing SVG parts into SVG-defined irregular stock.

This repository follows the structure of [`blib-la/runpod-worker-helloworld`](https://github.com/blib-la/runpod-worker-helloworld.git): RunPod starts `src/start.sh`, which launches `src/rp_handler.py`. The handler reads `job["input"]` and passes it to [`justingeeslin/packaide-irregular-stock`](https://github.com/justingeeslin/packaide-irregular-stock).

## Job Input

Send either one stock SVG:

```json
{
  "input": {
    "stock_svg": "<svg viewBox=\"0 0 2.5 2.5\" width=\"2.5\" height=\"2.5\"><circle id=\"stock\" cx=\"1.25\" cy=\"1.25\" r=\"1.25\" /></svg>",
    "parts_svg": "<svg viewBox=\"0 0 1 1\" width=\"1\" height=\"1\"><circle id=\"part\" cx=\"0.5\" cy=\"0.5\" r=\"0.35\" /></svg>",
    "tolerance": 0.03,
    "offset": 0,
    "rotations": 1,
    "persist": false
  }
}
```

Or multiple stock SVGs:

```json
{
  "input": {
    "stock_svgs": ["<svg ...></svg>", "<svg ...></svg>"],
    "shapes_svg": "<svg ...></svg>",
    "partial_solution": true
  }
}
```

`parts_svg` and `shapes_svg` are aliases. Supported Packaide options are `offset`, `tolerance`, `partial_solution`, `rotations`, `persist`, `include_stock`, and `stock_inset`. You can pass those options at the top level or inside `pack_options`.

The worker returns:

```json
{
  "outputs": [
    {
      "sheet_index": 0,
      "svg": "<svg>...</svg>"
    }
  ],
  "placed": 1,
  "unplaced": 0,
  "svg": "<svg>...</svg>"
}
```

`svg` is included as a convenience when there is exactly one output sheet.

## Local Tests

The unit tests mock the native Packaide adapter so the handler contract can be checked without compiling CGAL/Boost.Python:

```bash
python3 -m unittest discover
```

## Build

The component requires Python 3.14 and builds Packaide's native extension from `justingeeslin/Packaide@develop`. The Dockerfile therefore uses `python:3.14-slim`, installs CGAL build dependencies in a builder stage, builds Boost.Python for Python 3.14, installs the Python dependencies into `/opt/venv`, then copies only the runtime pieces into the final image.

The build emits milestone lines prefixed with `===`, including:

- `=== installing native build dependencies`
- `=== compiling and installing Boost.Python`
- `=== verifying native Packaide and RunPod imports`
- `=== verifying runtime imports and handler syntax`

If a managed builder only shows the clone/cache messages and none of those markers, the failure is happening before Dockerfile execution or the platform is suppressing Docker build output.

Build for RunPod:

```bash
docker build -t packaide-irregular-stock-worker:latest --platform linux/amd64 .
```

For an Apple Silicon local smoke build, use:

```bash
docker build -t packaide-irregular-stock-worker:dev --platform linux/arm64 .
```

Then mount the sample input:

```bash
docker run --rm -v "$PWD/test_input.json:/test_input.json:ro" packaide-irregular-stock-worker:dev
```

updating dependencies; trigger a build please