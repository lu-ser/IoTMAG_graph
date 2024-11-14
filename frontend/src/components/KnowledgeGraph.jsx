import React from "react";
import { ForceGraph2D } from "react-force-graph";

const KnowledgeGraph = ({ data }) => {
  const graphData = {
    nodes: data.nodes.map(node => ({
      ...node,
      color: getNodeColor(node.type),
      size: 6,
      x: Math.random() * 200 - 100,
      y: Math.random() * 200 - 100
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

  return (
    <div className="w-full h-screen bg-gray-50">
      <div className="p-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center mb-4">
            <span className="text-sm text-gray-600">
              Trascina i nodi per spostarli. Le posizioni verranno mantenute.
            </span>
          </div>
          
          <div className="h-96 border rounded-lg overflow-hidden">
            <ForceGraph2D
              graphData={graphData}
              nodeLabel={node => `${node.type}: ${node.name}`}
              linkLabel={link => link.label}
              nodeCanvasObject={(node, ctx, globalScale) => {
                ctx.beginPath();
                ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
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

                // Disegna la linea
                ctx.beginPath();
                ctx.moveTo(start.x, start.y);
                ctx.lineTo(end.x, end.y);
                ctx.strokeStyle = '#666666';
                ctx.lineWidth = 0.5;
                ctx.stroke();

                // Calcola il punto medio per le etichette
                const midX = (start.x + end.x) / 2;
                const midY = (start.y + end.y) / 2;

                const angle = Math.atan2(end.y - start.y, end.x - start.x);
                const dist = Math.sqrt(
                  Math.pow(end.x - start.x, 2) + 
                  Math.pow(end.y - start.y, 2)
                );

                // Disegna il tipo di relazione
                if (dist > 30) {
                  ctx.save();
                  ctx.translate(midX, midY);
                  ctx.rotate(angle);
                  
                  ctx.font = '3px sans-serif';
                  const typeWidth = ctx.measureText(link.type).width;
                  ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                  ctx.fillRect(
                    -typeWidth/2 - 2,
                    -8,
                    typeWidth + 4,
                    6
                  );
                  
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = '#666';
                  ctx.fillText(link.type, 0, -5);
                  
                  ctx.restore();
                }

                // Disegna il peso
                const weight = link.weight.toFixed(2);
                ctx.font = '3px sans-serif';
                const weightWidth = ctx.measureText(weight).width;
                
                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                ctx.fillRect(
                  midX - weightWidth/2 - 2,
                  midY - 2,
                  weightWidth + 4,
                  6
                );
                
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#666';
                ctx.fillText(weight, midX, midY);
              }}
              backgroundColor="#ffffff"
              enableNodeDrag={true}
              enableZoom={true}
              enablePanInteraction={true}
              cooldownTime={0}
              onNodeDragEnd={node => {
                node.fx = node.x;
                node.fy = node.y;
              }}
              onEngineStop={() => {
                graphData.nodes.forEach(node => {
                  if (node.fx === undefined) {
                    node.fx = node.x;
                    node.fy = node.y;
                  }
                });
              }}
              d3VelocityDecay={0.9}
              warmupTicks={0}
              d3Force="charge"
              d3ForceStrength={-200}
              linkDistance={50}
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-4">
            {Object.entries({
              person: 'Persone',
              topic: 'Argomenti',
              interest: 'Interessi',
              activity: 'Attività',
              skill: 'Competenze',
              tool: 'Strumenti',
              concept: 'Concetti',
              organization: 'Organizzazioni'
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