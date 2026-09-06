import React, { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Interactive polygon drawing canvas for defining virtual zone boundaries.
 * Overlays an SVG editor on a frozen camera frame snapshot.
 *
 * Supports two modes:
 * 1. Quad Mode — starts with a default 4-vertex rectangle; drag to adjust.
 * 2. Draw Mode — click to place vertices freehand; close polygon to edit.
 *
 * All coordinates are in native video resolution (e.g. 1280×720).
 */
export function ZoneDrawingCanvas({
  cameraId,
  imageUrl,
  zoneType = 'restricted',
  onCoordinatesChange,
  initialCoordinates = null,
}) {
  const svgRef = useRef(null);
  const imgRef = useRef(null);

  // Native video resolution (read from the loaded image or defaults to 1280x720)
  const [nativeWidth, setNativeWidth] = useState(1280);
  const [nativeHeight, setNativeHeight] = useState(720);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Polygon vertices in native resolution coordinates [{x, y}, ...]
  // Seed with default 4-vertex quad immediately so canvas is never blank
  const [vertices, setVertices] = useState(() => {
    if (initialCoordinates && initialCoordinates.length >= 3) {
      return initialCoordinates.map((p) => ({ x: Math.round(p.x), y: Math.round(p.y) }));
    }
    return [
      { x: 256, y: 144 },
      { x: 1024, y: 144 },
      { x: 1024, y: 576 },
      { x: 256, y: 576 },
    ];
  });

  // Interaction state
  const [mode, setMode] = useState('quad'); // 'quad' | 'draw'
  const [isClosed, setIsClosed] = useState(true);
  const [draggingIdx, setDraggingIdx] = useState(null);
  const [hoveredIdx, setHoveredIdx] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);
  const [cursorPos, setCursorPos] = useState(null); // native coords under cursor

  // Snapshot URL with cache buster
  const [snapshotUrl, setSnapshotUrl] = useState(imageUrl);

  // Update snapshotUrl when imageUrl prop changes
  useEffect(() => {
    setSnapshotUrl(imageUrl);
  }, [imageUrl]);

  // ── Coordinate conversion ─────────────────────────────────────────
  const clientToSvg = useCallback(
    (clientX, clientY) => {
      const svg = svgRef.current;
      if (!svg) return null;
      const pt = svg.createSVGPoint();
      pt.x = clientX;
      pt.y = clientY;
      const ctm = svg.getScreenCTM();
      if (!ctm) return null;
      const svgPt = pt.matrixTransform(ctm.inverse());
      return {
        x: Math.round(Math.max(0, Math.min(nativeWidth, svgPt.x))),
        y: Math.round(Math.max(0, Math.min(nativeHeight, svgPt.y))),
      };
    },
    [nativeWidth, nativeHeight],
  );

  // ── Image loaded handler ──────────────────────────────────────────
  const handleImageLoad = useCallback(
    (e) => {
      const img = e.target;
      const w = img.naturalWidth || 1280;
      const h = img.naturalHeight || 720;
      setNativeWidth((prevW) => {
        setNativeHeight((prevH) => {
          if (!initialCoordinates && (w !== prevW || h !== prevH)) {
            const insetX = Math.round(w * 0.2);
            const insetY = Math.round(h * 0.2);
            setVertices([
              { x: insetX, y: insetY },
              { x: w - insetX, y: insetY },
              { x: w - insetX, y: h - insetY },
              { x: insetX, y: h - insetY },
            ]);
            setIsClosed(true);
          }
          return h;
        });
        return w;
      });
      setImageLoaded(true);
    },
    [initialCoordinates],
  );

  const handleImageError = useCallback(() => {
    setImageLoaded(true);
  }, []);

  // Check if image is already cached / complete
  useEffect(() => {
    if (!snapshotUrl) {
      setImageLoaded(true);
      return;
    }
    if (imgRef.current && imgRef.current.complete) {
      if (imgRef.current.naturalWidth > 0) {
        handleImageLoad({ target: imgRef.current });
      } else {
        handleImageError();
      }
    }
  }, [snapshotUrl, handleImageLoad, handleImageError]);

  // ── Propagate coordinate changes ──────────────────────────────────
  useEffect(() => {
    if (onCoordinatesChange && isClosed && vertices.length >= 3) {
      onCoordinatesChange(vertices);
    }
  }, [vertices, isClosed, onCoordinatesChange]);

  // ── Switch to Draw Mode ───────────────────────────────────────────
  const switchToDrawMode = useCallback(() => {
    setMode('draw');
    setVertices([]);
    setIsClosed(false);
    setDraggingIdx(null);
    setHoveredIdx(null);
    setHoveredEdge(null);
    if (onCoordinatesChange) onCoordinatesChange([]);
  }, [onCoordinatesChange]);

  // ── Switch to Quad Mode ───────────────────────────────────────────
  const switchToQuadMode = useCallback(() => {
    setMode('quad');
    const insetX = Math.round(nativeWidth * 0.2);
    const insetY = Math.round(nativeHeight * 0.2);
    const defaultQuad = [
      { x: insetX, y: insetY },
      { x: nativeWidth - insetX, y: insetY },
      { x: nativeWidth - insetX, y: nativeHeight - insetY },
      { x: insetX, y: nativeHeight - insetY },
    ];
    setVertices(defaultQuad);
    setIsClosed(true);
    setDraggingIdx(null);
    setHoveredIdx(null);
    setHoveredEdge(null);
  }, [nativeWidth, nativeHeight]);

  // ── Refresh snapshot ──────────────────────────────────────────────
  const refreshSnapshot = useCallback(() => {
    const base = imageUrl.split('?')[0];
    setSnapshotUrl(`${base}?t=${Date.now()}`);
    setImageLoaded(false);
  }, [imageUrl]);

  // ── SVG mouse handlers ────────────────────────────────────────────
  const handleSvgMouseDown = useCallback(
    (e) => {
      if (e.button !== 0) return; // left click only
      const pt = clientToSvg(e.clientX, e.clientY);
      if (!pt) return;

      // If in draw mode and polygon is not closed
      if (mode === 'draw' && !isClosed) {
        // Check if clicking near the first vertex to close
        if (vertices.length >= 3) {
          const first = vertices[0];
          const dist = Math.sqrt((pt.x - first.x) ** 2 + (pt.y - first.y) ** 2);
          // Snap distance scales with resolution
          const snapDist = Math.max(12, Math.min(nativeWidth, nativeHeight) * 0.015);
          if (dist < snapDist) {
            setIsClosed(true);
            return;
          }
        }
        // Place new vertex
        setVertices((prev) => [...prev, pt]);
        return;
      }

      // If polygon is closed, check if clicking a vertex to start drag
      // (vertex hit detection is handled by the vertex circle onMouseDown)
    },
    [mode, isClosed, vertices, clientToSvg, nativeWidth, nativeHeight],
  );

  const handleSvgMouseMove = useCallback(
    (e) => {
      const pt = clientToSvg(e.clientX, e.clientY);
      if (!pt) return;
      setCursorPos(pt);

      if (draggingIdx !== null) {
        setVertices((prev) => {
          const updated = [...prev];
          updated[draggingIdx] = pt;
          return updated;
        });
      }
    },
    [clientToSvg, draggingIdx],
  );

  const handleSvgMouseUp = useCallback(() => {
    setDraggingIdx(null);
  }, []);

  const handleSvgDoubleClick = useCallback(
    (e) => {
      if (mode === 'draw' && !isClosed && vertices.length >= 3) {
        e.preventDefault();
        setIsClosed(true);
      }
    },
    [mode, isClosed, vertices.length],
  );

  // ── Vertex interactions ───────────────────────────────────────────
  const handleVertexMouseDown = useCallback(
    (e, idx) => {
      e.stopPropagation();
      if (e.button !== 0) return;
      if (!isClosed) return;
      setDraggingIdx(idx);
    },
    [isClosed],
  );

  const handleVertexContextMenu = useCallback(
    (e, idx) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isClosed) return;
      if (vertices.length <= 3) return; // minimum 3 vertices
      setVertices((prev) => prev.filter((_, i) => i !== idx));
    },
    [isClosed, vertices.length],
  );

  // ── Edge midpoint insertion ───────────────────────────────────────
  const handleMidpointClick = useCallback(
    (e, edgeIdx) => {
      e.stopPropagation();
      if (!isClosed) return;
      const nextIdx = (edgeIdx + 1) % vertices.length;
      const midX = Math.round((vertices[edgeIdx].x + vertices[nextIdx].x) / 2);
      const midY = Math.round((vertices[edgeIdx].y + vertices[nextIdx].y) / 2);
      setVertices((prev) => {
        const updated = [...prev];
        updated.splice(nextIdx, 0, { x: midX, y: midY });
        return updated;
      });
      // Start dragging the newly inserted vertex
      setDraggingIdx(nextIdx);
    },
    [isClosed, vertices],
  );

  // ── Global mouse up listener (for drag ending outside SVG) ────────
  useEffect(() => {
    const handleGlobalUp = () => setDraggingIdx(null);
    window.addEventListener('mouseup', handleGlobalUp);
    return () => window.removeEventListener('mouseup', handleGlobalUp);
  }, []);

  // ── Render helpers ────────────────────────────────────────────────
  const isRestricted = zoneType === 'restricted';
  const strokeColor = isRestricted ? '#ef4444' : '#00daf3';
  const fillColor = isRestricted ? 'rgba(239, 68, 68, 0.16)' : 'rgba(0, 218, 243, 0.12)';
  const vertexRadius = Math.max(4, Math.min(nativeWidth, nativeHeight) * 0.007);
  const crosshairSize = vertexRadius * 1.8;
  const hitRadius = vertexRadius * 2.5;

  // Build polygon points string
  const pointsStr = vertices.map((p) => `${p.x},${p.y}`).join(' ');

  // Compute edge midpoints for ghost nodes
  const midpoints =
    isClosed && vertices.length >= 3
      ? vertices.map((v, i) => {
          const next = vertices[(i + 1) % vertices.length];
          return {
            x: Math.round((v.x + next.x) / 2),
            y: Math.round((v.y + next.y) / 2),
            edgeIdx: i,
          };
        })
      : [];

  // Determine cursor style
  let svgCursor = 'crosshair';
  if (isClosed && draggingIdx !== null) svgCursor = 'grabbing';
  else if (isClosed && hoveredIdx !== null) svgCursor = 'grab';
  else if (isClosed && hoveredEdge !== null) svgCursor = 'cell';
  else if (isClosed) svgCursor = 'default';

  return (
    <div className="zone-editor-main">
      {/* Toolbar */}
      <div className="zone-editor-toolbar">
        <div className="zone-editor-toolbar-group">
          <button
            type="button"
            className={`zone-mode-toggle ${mode === 'quad' && isClosed ? 'active' : ''}`}
            onClick={switchToQuadMode}
            title="Reset to default quadrilateral"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
              crop_square
            </span>
            Quad Mode
          </button>
          <button
            type="button"
            className={`zone-mode-toggle ${mode === 'draw' ? 'active' : ''}`}
            onClick={switchToDrawMode}
            title="Clear and draw freehand polygon"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
              draw
            </span>
            Draw Mode
          </button>

          <span
            style={{
              width: '1px',
              height: '18px',
              background: 'var(--hairline-divider)',
              margin: '0 4px',
            }}
          />

          <button type="button" className="zone-mode-toggle" onClick={refreshSnapshot} title="Refresh camera snapshot">
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>
              refresh
            </span>
            Refresh
          </button>
        </div>

        <div className="zone-editor-toolbar-group">
          <span
            style={{
              fontSize: '10px',
              color: 'var(--text-dim)',
            }}
          >
            {nativeWidth}×{nativeHeight}
          </span>
        </div>
      </div>

      {/* Canvas */}
      <div className="zone-editor-canvas-wrapper hud-grid-bg">
        {snapshotUrl ? (
          <img
            ref={imgRef}
            src={snapshotUrl}
            alt="Camera snapshot for zone definition"
            onLoad={handleImageLoad}
            onError={handleImageError}
            draggable={false}
          />
        ) : null}

        <svg
          ref={svgRef}
          viewBox={`0 0 ${nativeWidth} ${nativeHeight}`}
            preserveAspectRatio="xMidYMid meet"
            style={{ cursor: svgCursor }}
            onMouseDown={handleSvgMouseDown}
            onMouseMove={handleSvgMouseMove}
            onMouseUp={handleSvgMouseUp}
            onDoubleClick={handleSvgDoubleClick}
            onContextMenu={(e) => e.preventDefault()}
          >
            {/* Closed polygon fill + stroke */}
            {isClosed && vertices.length >= 3 && (
              <polygon
                points={pointsStr}
                fill={fillColor}
                stroke={strokeColor}
                strokeWidth={Math.max(1.5, nativeWidth * 0.0015)}
              />
            )}

            {/* Open polyline while drawing */}
            {!isClosed && vertices.length >= 2 && (
              <polyline
                points={pointsStr}
                fill="none"
                stroke={strokeColor}
                strokeWidth={Math.max(1.5, nativeWidth * 0.0015)}
                strokeDasharray={`${Math.max(4, nativeWidth * 0.004)},${Math.max(3, nativeWidth * 0.003)}`}
              />
            )}

            {/* Rubberband line from last vertex to cursor (draw mode) */}
            {!isClosed && mode === 'draw' && vertices.length > 0 && cursorPos && (
              <line
                x1={vertices[vertices.length - 1].x}
                y1={vertices[vertices.length - 1].y}
                x2={cursorPos.x}
                y2={cursorPos.y}
                stroke={strokeColor}
                strokeWidth={Math.max(1, nativeWidth * 0.001)}
                strokeDasharray={`${Math.max(4, nativeWidth * 0.004)},${Math.max(3, nativeWidth * 0.003)}`}
                opacity={0.6}
              />
            )}

            {/* Edge midpoint ghost nodes (visible on closed polygon) */}
            {midpoints.map((mp) => (
              <circle
                key={`mid-${mp.edgeIdx}`}
                cx={mp.x}
                cy={mp.y}
                r={vertexRadius * 0.8}
                fill="rgba(255, 255, 255, 0.15)"
                stroke={strokeColor}
                strokeWidth={Math.max(0.5, nativeWidth * 0.0006)}
                style={{ cursor: 'cell' }}
                opacity={hoveredEdge === mp.edgeIdx ? 0.9 : 0.3}
                onMouseEnter={() => setHoveredEdge(mp.edgeIdx)}
                onMouseLeave={() => setHoveredEdge(null)}
                onMouseDown={(e) => handleMidpointClick(e, mp.edgeIdx)}
              />
            ))}

            {/* Vertex nodes with tactical crosshair reticles */}
            {vertices.map((v, idx) => {
              const isFirst = idx === 0;
              const isHovered = hoveredIdx === idx;
              const isDragging = draggingIdx === idx;
              // In draw mode, highlight first vertex as snap target
              const isSnapTarget = !isClosed && mode === 'draw' && isFirst && vertices.length >= 3;

              return (
                <g key={`v-${idx}`}>
                  {/* Crosshair lines */}
                  <line
                    x1={v.x - crosshairSize}
                    y1={v.y}
                    x2={v.x + crosshairSize}
                    y2={v.y}
                    stroke={isSnapTarget ? '#10b981' : strokeColor}
                    strokeWidth={Math.max(1, nativeWidth * 0.001)}
                    opacity={isHovered || isDragging ? 1 : 0.7}
                  />
                  <line
                    x1={v.x}
                    y1={v.y - crosshairSize}
                    x2={v.x}
                    y2={v.y + crosshairSize}
                    stroke={isSnapTarget ? '#10b981' : strokeColor}
                    strokeWidth={Math.max(1, nativeWidth * 0.001)}
                    opacity={isHovered || isDragging ? 1 : 0.7}
                  />
                  {/* Center dot */}
                  <circle
                    cx={v.x}
                    cy={v.y}
                    r={vertexRadius * (isHovered || isDragging ? 1.3 : 1)}
                    fill={isSnapTarget ? '#10b981' : '#ffffff'}
                    stroke={isSnapTarget ? '#10b981' : strokeColor}
                    strokeWidth={Math.max(0.8, nativeWidth * 0.0008)}
                  />
                  {/* Invisible hit area for easier grabbing */}
                  <circle
                    cx={v.x}
                    cy={v.y}
                    r={hitRadius}
                    fill="transparent"
                    style={{ cursor: isClosed ? 'grab' : 'default' }}
                    onMouseEnter={() => setHoveredIdx(idx)}
                    onMouseLeave={() => setHoveredIdx(null)}
                    onMouseDown={(e) => handleVertexMouseDown(e, idx)}
                    onContextMenu={(e) => handleVertexContextMenu(e, idx)}
                  />
                  {/* Snap ring pulse for first vertex in draw mode */}
                  {isSnapTarget && (
                    <circle
                      cx={v.x}
                      cy={v.y}
                      r={hitRadius}
                      fill="none"
                      stroke="#10b981"
                      strokeWidth={Math.max(0.5, nativeWidth * 0.0005)}
                      opacity={0.5}
                    >
                      <animate
                        attributeName="r"
                        from={hitRadius}
                        to={hitRadius * 1.8}
                        dur="1.2s"
                        repeatCount="indefinite"
                      />
                      <animate attributeName="opacity" from="0.5" to="0" dur="1.2s" repeatCount="indefinite" />
                    </circle>
                  )}
                </g>
              );
            })}
          </svg>

        {/* Draw mode instruction banner */}
        {mode === 'draw' && !isClosed && (
          <div className="zone-draw-instruction">
            <span className="material-symbols-outlined">touch_app</span>
            {vertices.length === 0
              ? 'Click to place first vertex'
              : vertices.length < 3
                ? `Place at least ${3 - vertices.length} more ${vertices.length === 2 ? 'vertex' : 'vertices'}`
                : 'Click first vertex or double-click to close polygon'}
          </div>
        )}

        {/* Subtle loading state badge */}
        {!imageLoaded && snapshotUrl && (
          <div
            style={{
              position: 'absolute',
              top: '10px',
              left: '10px',
              padding: '3px 8px',
              background: 'rgba(0, 0, 0, 0.75)',
              border: '1px solid var(--glass-border)',
              fontSize: '10px',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
            }}
          >
            Fetching camera frame…
          </div>
        )}

        {/* Live coordinate HUD */}
        {cursorPos && (
          <div className="zone-coord-hud">
            <span className="coord-label">XY</span>
            [{cursorPos.x}, {cursorPos.y}]
          </div>
        )}

        {/* Vertex count */}
        <div className="zone-vertex-count">
          {vertices.length} {vertices.length === 1 ? 'vertex' : 'vertices'}
          {isClosed ? ' · closed' : ' · open'}
        </div>
      </div>
    </div>
  );
}
