import React, { useCallback, useMemo } from "react";
import { ForceGraph2D } from "react-force-graph";

const KnowledgeGraph = ({ data }) => {
  const graphData = useMemo(() => ({
    nodes: data.nodes.map(node => ({
      ...node,
      color: getNodeColor(node.type),
      size: 6
    })),
    links: data.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      label: `${edge.type} (${edge.weight.toFixed(2)})`,
      weight: edge.weight,
      type: edge.type
    }))
  }), [data]);

  function getNodeColor(type) {
    const colors = {
      person: '#ff6b6b',
      topic: '#4ecdc4',
      interest: '#45b7d1',
      activity: '#96ceb4',
      skill: '#ffd93d',
      tool: '#6c5ce7',
      concept: '#a8e6cf',
      organization: '#ff8b94',
      default: '#666666'
    };
    return colors[type?.toLowerCase()] || colors.default;
  }

  const handleNodeClick = useCallback(node => {
    console.log('Node details:', node);
  }, []);

  const drawLink = useCallback((link, ctx, globalScale) => {
    const start = link.source;
    const end = link.target;

    // Calculate control points for a quadratic curve
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Make the curve higher for longer distances
    const curvature = Math.min(0.2, 30 / distance);
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2;
    
    // Calculate normal vector for curve control point
    const nx = -dy;
    const ny = dx;
    const normalization = Math.sqrt(nx * nx + ny * ny);
    
    // Control point
    const cpX = midX + (nx / normalization) * distance * curvature;
    const cpY = midY + (ny / normalization) * distance * curvature;

    // Draw curved path
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.quadraticCurveTo(cpX, cpY, end.x, end.y);
    ctx.strokeStyle = `rgba(153, 153, 153, ${Math.max(0.2, link.weight)})`;
    ctx.lineWidth = Math.max(0.5, link.weight * 2);
    ctx.stroke();

    // Draw arrow at the end
    const arrowLength = 6;
    const arrowWidth = 4;
    const angle = Math.atan2(end.y - cpY, end.x - cpX);
    
    ctx.beginPath();
    ctx.moveTo(end.x, end.y);
    ctx.lineTo(
      end.x - arrowLength * Math.cos(angle - Math.PI / 6),
      end.y - arrowLength * Math.sin(angle - Math.PI / 6)
    );
    ctx.lineTo(
      end.x - arrowLength * Math.cos(angle + Math.PI / 6),
      end.y - arrowLength * Math.sin(angle + Math.PI / 6)
    );
    ctx.closePath();
    ctx.fillStyle = '#999';
    ctx.fill();

    // Calculate label position along the curve
    const labelX = cpX;
    const labelY = cpY - 5;

    // Draw label background
    const type = link.type;
    const weight = link.weight.toFixed(2);
    ctx.font = '3px sans-serif';
    const typeWidth = ctx.measureText(type).width;
    const weightWidth = ctx.measureText(weight).width;
    const padding = 2;

    // Draw backgrounds for both labels
    ctx.fillStyle = 'white';
    ctx.fillRect(
      labelX - typeWidth/2 - padding,
      labelY - 6,
      typeWidth + padding * 2,
      5
    );
    ctx.fillRect(
      labelX - weightWidth/2 - padding,
      labelY + 1,
      weightWidth + padding * 2,
      5
    );

    // Draw labels
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#666';
    ctx.fillText(type, labelX, labelY - 4);
    ctx.fillText(weight, labelX, labelY + 4);
  }, []);

  return (
    <div className="w-full bg-gray-50">
      <div className="p-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-gray-600">
              Click nodes to see details. Edge labels show relationship type and weight.
            </span>
          </div>
          
          <div className="h-96 border rounded-lg overflow-hidden">
            <ForceGraph2D
              graphData={graphData}
              nodeLabel={node => `${node.type}: ${node.name}\nAttributes: ${JSON.stringify(node.attributes, null, 2)}`}
              linkLabel={link => link.label}
              onNodeClick={handleNodeClick}
              nodeCanvasObject={(node, ctx, globalScale) => {
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI, false);
                ctx.fillStyle = node.color;
                ctx.fill();

                if (globalScale >= 1.5) {
                  const label = `${node.name} (${node.type})`;
                  ctx.font = '4px sans-serif';
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = '#000';
                  ctx.fillText(label, node.x, node.y + 8);
                }
              }}
              linkCanvasObject={drawLink}
              linkDirectionalParticles={2}
              linkDirectionalParticleSpeed={0.005}
              backgroundColor="#ffffff"
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.3}
              cooldownTicks={100}
              linkDistance={100}
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-4">
            {Object.entries({
              person: 'People',
              topic: 'Topics',
              interest: 'Interests',
              activity: 'Activities',
              skill: 'Skills',
              tool: 'Tools',
              concept: 'Concepts',
              organization: 'Organizations'
            }).map(([type, label]) => (
              <div key={type} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: getNodeColor(type) }}
                />
                <span className="text-sm text-gray-600">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;