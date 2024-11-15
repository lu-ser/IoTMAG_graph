import React from "react";
import { ForceGraph2D } from "react-force-graph";

const KnowledgeGraph = ({ data }) => {
  const graphRef = React.useRef(null);
  const [simulationRunning, setSimulationRunning] = React.useState(true);
  const [selectedNode, setSelectedNode] = React.useState(null);

  // Formatta il valore dell'attributo rimuovendo i doppi apici
  const formatAttributeValue = (value) => {
    if (typeof value === 'string') {
      return value.replace(/^"(.*)"$/, '$1');
    }
    return value;
  };

  // Formatta il nome dell'attributo per la visualizzazione
  const formatAttributeName = (name) => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Funzione per aggiungere una leggera forza casuale
  const addRandomForce = (node) => {
    if (!node.fx && !node.fy) { // Solo per nodi non fissati
      const angle = Math.random() * 2 * Math.PI;
      const force = 0.3; // Forza ridotta per movimento più sottile
      
      node.vx = (node.vx || 0) + Math.cos(angle) * force;
      node.vy = (node.vy || 0) + Math.sin(angle) * force;
    }
  };

  // Effetto per il movimento continuo ma controllato
  React.useEffect(() => {
    if (!simulationRunning) return;

    const interval = setInterval(() => {
      if (graphRef.current) {
        const nodes = graphRef.current.graphData().nodes;
        nodes.forEach(addRandomForce);
        graphRef.current.d3ReheatSimulation();
      }
    }, 2000); // Intervallo più lungo per movimento più graduale

    return () => clearInterval(interval);
  }, [simulationRunning]);

  // Mantiene traccia delle posizioni dei nodi
  const [nodePositions, setNodePositions] = React.useState({});

  // Inizializza le posizioni salvate per i nodi
  React.useEffect(() => {
    const positions = {};
    data.nodes.forEach(node => {
      if (nodePositions[node.id]) {
        positions[node.id] = nodePositions[node.id];
      }
    });
    setNodePositions(positions);
  }, [data.nodes]);

  const graphData = {
    nodes: data.nodes.map(node => ({
      ...node,
      color: getNodeColor(node.type),
      size: 8,
      // Applica le posizioni salvate se esistono
      ...(nodePositions[node.id] && {
        x: nodePositions[node.id].x,
        y: nodePositions[node.id].y,
        fx: nodePositions[node.id].x,
        fy: nodePositions[node.id].y
      })
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
      <div className="p-4 flex gap-4">
        <div className="flex-1">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-gray-600">
                Trascina i nodi per spostarli. Le posizioni verranno mantenute.
              </span>
            </div>
            
            <div className="h-128 border rounded-lg overflow-hidden relative">
              <ForceGraph2D
                ref={graphRef}
                width={1248}
                height={768}
                graphData={graphData}
                centerAt={[0,0]}
                zoom={1.5}
                nodeLabel={node => `${node.type}: ${node.name}`}
                linkLabel={link => link.label}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const nodeRadius = 8;
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false);
                  ctx.fillStyle = node.color;
                  ctx.fill();

                  ctx.strokeStyle = '#ffffff';
                  ctx.lineWidth = 1.5;
                  ctx.stroke();

                  if (globalScale >= 1.5) {
                    const label = `${node.name} (${node.type})`;
                    ctx.font = '5px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#000';
                    ctx.fillText(label, node.x, node.y + nodeRadius + 4);
                  }
                }}
                linkCanvasObject={(link, ctx) => {
                  const start = link.source;
                  const end = link.target;

                  ctx.beginPath();
                  ctx.moveTo(start.x, start.y);
                  ctx.lineTo(end.x, end.y);
                  ctx.strokeStyle = '#999999';
                  ctx.lineWidth = 0.3;
                  ctx.stroke();

                  const midX = (start.x + end.x) / 2;
                  const midY = (start.y + end.y) / 2;
                  const angle = Math.atan2(end.y - start.y, end.x - start.x);
                  const dist = Math.sqrt(
                    Math.pow(end.x - start.x, 2) + 
                    Math.pow(end.y - start.y, 2)
                  );

                  if (dist > 50) {
                    ctx.save();
                    ctx.translate(midX, midY);
                    ctx.rotate(angle);
                    
                    ctx.font = '3px sans-serif';
                    const typeWidth = ctx.measureText(link.type).width;
                    
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                    ctx.fillRect(
                      -typeWidth/2 - 2,
                      -8,
                      typeWidth + 4,
                      6
                    );
                    
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#444';
                    ctx.fillText(link.type, 0, -5);
                    
                    ctx.restore();
                  }

                  if (dist > 40) {
                    const weight = link.weight.toFixed(2);
                    ctx.font = '3px sans-serif';
                    const weightWidth = ctx.measureText(weight).width;
                    
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                    ctx.fillRect(
                      midX - weightWidth/2 - 2,
                      midY - 2,
                      weightWidth + 4,
                      6
                    );
                    
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#444';
                    ctx.fillText(weight, midX, midY);
                  }
                }}
                backgroundColor="#ffffff"
                enableNodeDrag={true}
                enableZoom={true}
                enablePanInteraction={true}
                cooldownTime={2000}
                onNodeDragEnd={node => {
                  node.fx = node.x;
                  node.fy = node.y;
                  // Salva la nuova posizione
                  setNodePositions(prev => ({
                    ...prev,
                    [node.id]: { x: node.x, y: node.y }
                  }));
                }}
                onNodeClick={(node) => {
                  setSelectedNode(node);
                }}
                d3Force={{
                  center: d3 => d3.forceCenter().strength(0.05),
                  charge: d3 => d3.forceManyBody()
                    .strength(-800)
                    .distanceMax(250),
                  collide: d3 => d3.forceCollide(50).strength(0.5),
                  link: d3 => d3.forceLink()
                    .distance(link => link.type === 'related' ? 200 : 150)
                    .strength(0.2)
                }}
                d3VelocityDecay={0.6}
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
                organization: 'Organizzazioni',
                default: 'Altro',
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

        {/* Pannello laterale per i dettagli del nodo */}
        {selectedNode && (
          <div className="w-[32rem] bg-white rounded-lg shadow p-6 h-fit min-h-[24rem]">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Dettagli Nodo</h2>
              <button 
                onClick={() => setSelectedNode(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: selectedNode.color }}
                  />
                  <h3 className="text-lg font-medium">{selectedNode.name}</h3>
                </div>
                <p className="text-sm text-gray-600">Tipo: {selectedNode.type}</p>
              </div>

              {selectedNode.attributes && Object.keys(selectedNode.attributes).length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Attributi</h4>
                  <div className="space-y-2">
                    {Object.entries(selectedNode.attributes).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm text-gray-600">{formatAttributeName(key)}:</span>
                        <span className="text-sm font-medium">{formatAttributeValue(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-sm text-gray-500">
                Creato il: {new Date(selectedNode.timestamp).toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraph;