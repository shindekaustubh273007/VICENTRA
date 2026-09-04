import React from 'react';

/**
 * Tactical SVG-based overlay component for rendering polygon zones over a camera frame.
 * Renders precision military C2 HUD wireframes with crosshair vertex reticles.
 */
export function ZoneOverlay({ zones = [], width = 640, height = 360 }) {
  if (!zones || zones.length === 0) return null;

  return (
    <svg
      className="zone-overlay-svg"
      viewBox={`0 0 ${width} ${height}`}
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
              strokeWidth="1.5"
              strokeDasharray={isRestricted ? 'none' : '4,3'}
            />
            {zone.coordinates.map((pt, idx) => (
              <g key={idx}>
                {/* Precision Tactical Crosshair Node */}
                <line x1={pt.x - 4} y1={pt.y} x2={pt.x + 4} y2={pt.y} stroke={strokeColor} strokeWidth="1.5" />
                <line x1={pt.x} y1={pt.y - 4} x2={pt.x} y2={pt.y + 4} stroke={strokeColor} strokeWidth="1.5" />
                <circle cx={pt.x} cy={pt.y} r="2" fill="#ffffff" />
              </g>
            ))}
            {/* Centroid Tactical Callout Tag */}
            <rect
              x={centerX - 45}
              y={centerY - 9}
              width="90"
              height="18"
              fill="rgba(8, 8, 10, 0.88)"
              stroke={strokeColor}
              strokeWidth="1"
            />
            <text
              x={centerX}
              y={centerY + 3}
              fill="#ffffff"
              fontSize="9"
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
