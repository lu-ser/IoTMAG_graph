import { useState, useEffect } from 'react';
import KnowledgeGraph from './components/KnowledgeGraph';

// Rimuovi eventuali slash finali dall'URL
const API_URL = import.meta.env.VITE_API_URL?.replace(/\/+$/, '') || 'http://localhost:8000';

function App() {
  const [graphData, setGraphData] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [timeFilter, setTimeFilter] = useState('now');
  const [messageTime, setMessageTime] = useState('now');
  const [error, setError] = useState(null);

  const timeFilters = [
    { value: 'now', label: 'Current' },
    { value: '1h', label: 'Last Hour' },
    { value: '1d', label: 'Last Day' },
    { value: '1w', label: 'Last Week' },
    { value: '1m', label: 'Last Month' },
  ];

  const getTimestamp = (timeOffset) => {
    const now = new Date();
    switch (timeOffset) {
      case 'now':
        return now;
      case '1h':
        return new Date(now.getTime() - 60 * 60 * 1000);
      case '1d':
        return new Date(now.getTime() - 24 * 60 * 60 * 1000);
      case '1w':
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      case '1m':
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      default:
        return now;
    }
  };

  const fetchGraphData = async () => {
    try {
      setError(null);
      console.log(`Fetching graph data with time_filter=${timeFilter}`);
      const response = await fetch(`${API_URL}/graph?time_filter=${timeFilter}`, {
        headers: {                               // <-- MODIFICA QUI
          'Accept': 'application/json',
          'ngrok-skip-browser-warning': 'true'   // <-- AGGIUNGI QUESTA RIGA
        }
      });

      if (!response.ok) {
        const text = await response.text();
        console.log('Error response text:', text);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const text = await response.text();
      console.log('Response text:', text);

      const data = JSON.parse(text);
      console.log('Parsed data:', data);
      
      setGraphData(data);
    } catch (error) {
      console.error('Full error:', error);
      setError(error.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const timestamp = getTimestamp(messageTime).toISOString();
      console.log('Sending message with timestamp:', timestamp);
      
      const response = await fetch(`${API_URL}/process-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'ngrok-skip-browser-warning': 'true'   // <-- AGGIUNGI QUESTA RIGA
        },
        body: JSON.stringify({ 
          text: message,
          timestamp: timestamp
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process message');
      }

      await fetchGraphData();
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Aggiorniamo il grafo quando cambia il filtro temporale
  useEffect(() => {
    console.log('Time filter changed to:', timeFilter);
    fetchGraphData();
  }, [timeFilter]);

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">
              Knowledge Graph
            </h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">View Window:</span>
                <select
                  value={timeFilter}
                  onChange={(e) => setTimeFilter(e.target.value)}
                  className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
                >
                  {timeFilters.map(filter => (
                    <option key={filter.value} value={filter.value}>
                      {filter.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 px-4">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex-1">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="Enter your message here..."
                  rows="3"
                />
              </div>
              <div className="flex flex-col gap-2">
                <div className="flex flex-col">
                  <label className="text-sm text-gray-600 mb-1">Message Time:</label>
                  <select
                    value={messageTime}
                    onChange={(e) => setMessageTime(e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2"
                  >
                    {timeFilters.map(filter => (
                      <option key={filter.value} value={filter.value}>
                        {filter.label}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={loading || !message}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
                >
                  {loading ? 'Processing...' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        </form>

        {graphData ? (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <div className="text-sm text-gray-600">
                Showing data from: {timeFilters.find(f => f.value === timeFilter)?.label}
                {graphData.nodes.length === 0 && (
                  <span className="ml-2 text-yellow-600">
                    (No data available for this time period)
                  </span>
                )}
              </div>
            </div>
            <KnowledgeGraph data={graphData} />
          </div>
        ) : (
          <div className="text-center p-4">Loading graph data...</div>
        )}
      </main>
    </div>
  );
}

export default App;