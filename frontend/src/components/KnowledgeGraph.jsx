import React, { useCallback } from "react";
import { ForceGraph2D } from "react-force-graph";

const KnowledgeGraph = ({ data }) => {
  const graphData = {
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
  };

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

  return (
    <div className="w-full h-screen bg-gray-50">
      <div className="p-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-gray-600">
              Click nodes to see details. Edge labels show relationship type and weight.
            </span>
          </div>
          
          <div className="h-[600px] border rounded-lg overflow-hidden">
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
              linkCanvasObject={(link, ctx) => {
                const start = link.source;
                const end = link.target;

                // Draw thin line
                ctx.beginPath();
                ctx.moveTo(start.x, start.y);
                ctx.lineTo(end.x, end.y);
                ctx.strokeStyle = '#999999';
                ctx.lineWidth = 0.5; // Linea molto sottile
                ctx.stroke();

                // Calculate middle point for the weight label
                const midX = (start.x + end.x) / 2;
                const midY = (start.y + end.y) / 2;

                // Draw background for better readability
                const weight = link.weight.toFixed(2);
                ctx.font = '3px sans-serif';
                const textWidth = ctx.measureText(weight).width;
                ctx.fillStyle = 'white';
                ctx.fillRect(
                  midX - textWidth/2 - 1,
                  midY - 2,
                  textWidth + 2,
                  4
                );

                // Draw relationship type and weight
                ctx.font = '3px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#666';
                
                // Draw weight number
                ctx.fillText(weight, midX, midY);

                // Calculate angle for relationship type
                const angle = Math.atan2(end.y - start.y, end.x - start.x);
                const dist = Math.sqrt(
                  Math.pow(end.x - start.x, 2) + 
                  Math.pow(end.y - start.y, 2)
                );

                // Draw relationship type if there's enough space
                if (dist > 30) {
                  ctx.save();
                  ctx.translate(midX, midY);
                  ctx.rotate(angle);
                  ctx.fillText(
                    link.type,
                    0,
                    -4 // Sposta il testo leggermente sopra la linea
                  );
                  ctx.restore();
                }
              }}
              backgroundColor="#ffffff"
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