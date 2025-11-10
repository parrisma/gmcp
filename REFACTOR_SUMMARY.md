# GraphData to GraphParams Refactoring

## Summary

Renamed `GraphData` class to `GraphParams` to better reflect its purpose as a parameter object for graph rendering rather than a data container.

## Changes Made

### New File
- **app/graph_params.py**: New module containing:
  - `GraphParams` class (renamed from `GraphData`)
  - `GraphData` backward compatibility alias

### Removed File
- **app/models.py**: Removed (replaced by graph_params.py)

### Updated Files

#### Core Application Files
- **app/web_server.py**: Updated import and type hints
- **app/mcp_server.py**: Updated import and type hints
- **app/render.py**: Updated import and type hints (legacy file)
- **app/render/renderer.py**: Updated import and type hints

#### Handler Files
- **app/handlers/base.py**: Updated TYPE_CHECKING import and method signature
- **app/handlers/line.py**: Updated TYPE_CHECKING import and method signature
- **app/handlers/scatter.py**: Updated TYPE_CHECKING import and method signature
- **app/handlers/bar.py**: Updated TYPE_CHECKING import and method signature

#### Validation
- **app/validation/validator.py**: Updated import and all method signatures

#### Documentation
All markdown files updated to use `GraphParams` in:
- Code examples
- API documentation
- References to the model

Files updated:
- README.md
- MCP_README.md
- docs/MCP_README.md
- docs/PROXY_MODE.md
- app/themes/README.md
- app/render/README.md

## Backward Compatibility

The `GraphData` name is preserved as an alias:
```python
GraphData = GraphParams
```

This ensures any external code using `GraphData` will continue to work without changes.

## Verification

- ✅ All lint errors resolved
- ✅ No import errors
- ✅ Type checking passes
- ✅ Documentation updated
- ✅ Backward compatibility maintained
