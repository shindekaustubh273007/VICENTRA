import React from 'react';

/**
 * Tactical SVG-based overlay component for rendering polygon zones over a camera frame.
 * Renders precision military C2 HUD wireframes with crosshair vertex reticles.
 */
export function ZoneOverlay({ zones = [], width = 1280, height = 720 }) {
  if (!zones || zones.length === 0) return null;

  const scale = Math.max(0.6, Math.min(width, height) / 720);
  const strokeW = Math.max(1.5, 2 * scale);
  const chSize = 5 * scale;
  const dotR = 2.5 * scale;
  const tagW = 100 * scale;
  const tagH = 22 * scale;
  const tagFont = Math.max(9, Math.round(11 * scale));

  return (
    <svg
      className="zone-overlay-svg"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      }}
    >
      {zones.map((zone) => {
        if (!zone.enabled || !zone.coordinates || zone.coordinates.length < 3) {
          return null;
        }

        const pointsStr = zone.coordinates.map((pt) => `${pt.x},${pt.y}`).join(' ');
        const isRestricted = zone.zone_type === 'restricted';

        const strokeColor = isRestricted ? '#ef4444' : '#00daf3';
        const fillColor = isRestricted ? 'rgba(239, 68, 68, 0.16)' : 'rgba(0, 218, 243, 0.10)';

        // Compute centroid for zone label
        const centerX = zone.coordinates.reduce((sum, p) => sum + p.x, 0) / zone.coordinates.length;
        const centerY = zone.coordinates.reduce((sum, p) => sum + p.y, 0) / zone.coordinates.length;

        return (
          <g key={zone.zone_id}>
            <polygon
              points={pointsStr}
              fill={fillColor}
              stroke={strokeColor}
              strokeWidth={strokeW}
              strokeDasharray={isRestricted ? 'none' : `${5 * scale},${3 * scale}`}
            />
            {zone.coordinates.map((pt, idx) => (
              <g key={idx}>
                {/* Precision Tactical Crosshair Node */}
                <line x1={pt.x - chSize} y1={pt.y} x2={pt.x + chSize} y2={pt.y} stroke={strokeColor} strokeWidth={strokeW} />
                <line x1={pt.x} y1={pt.y - chSize} x2={pt.x} y2={pt.y + chSize} stroke={strokeColor} strokeWidth={strokeW} />
                <circle cx={pt.x} cy={pt.y} r={dotR} fill="#ffffff" />
              </g>
            ))}
            {/* Centroid Tactical Callout Tag */}
            <rect
              x={centerX - tagW / 2}
              y={centerY - tagH / 2}
              width={tagW}
              height={tagH}
              fill="rgba(8, 8, 10, 0.88)"
              stroke={strokeColor}
              strokeWidth={Math.max(1, scale)}
              rx={2 * scale}
            />
            <text
              x={centerX}
              y={centerY + (tagFont * 0.35)}
              fill="#ffffff"
              fontSize={tagFont}
              fontFamily="JetBrains Mono, monospace"
              fontWeight="600"
              letterSpacing="0.5"
              textAnchor="middle"
            >
              {zone.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
