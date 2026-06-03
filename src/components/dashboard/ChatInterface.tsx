import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ClusterData {
  pods: {
    total: number;
    running: number;
    pending: number;
    failed: number;
  };
  pvcs: {
    total: number;
    bound: number;
    pending: number;
    lost: number;
  };
  nodes: {
    total: number;
    ready: number;
    notReady: number;
    schedulingDisabled: number;
  };
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your Kubernetes assistant. How can I help you with your cluster?',
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);
  
  const [inputValue, setInputValue] = useState('');
  const [clusterData, setClusterData] = useState<ClusterData | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch cluster data initially
  useEffect(() => {
    const fetchClusterData = async () => {
      try {
        const response = await fetch('/api/my/v1/cluster-monitor');
        const data = await response.json();
        
        if (!data.error) {
          // Process data to get summary statistics
          const processedData: ClusterData = {
            pods: {
              total: data.pods.items.length,
              running: data.pods.items.filter((pod: any) => pod.status === 'Running').length,
              pending: data.pods.items.filter((pod: any) => pod.status === 'Pending').length,
              failed: data.pods.items.filter((pod: any) => pod.status === 'Failed').length,
            },
            pvcs: {
              total: data.pvcs.items.length,
              bound: data.pvcs.items.filter((pvc: any) => pvc.status === 'Bound').length,
              pending: data.pvcs.items.filter((pvc: any) => pvc.status === 'Pending').length,
              lost: data.pvcs.items.filter((pvc: any) => pvc.status === 'Lost').length,
            },
            nodes: {
              total: data.nodes.items.length,
              ready: data.nodes.items.filter((node: any) => node.status === 'Ready').length,
              notReady: data.nodes.items.filter((node: any) => node.status === 'NotReady').length,
              schedulingDisabled: data.nodes.items.filter((node: any) => node.status === 'SchedulingDisabled').length,
            }
          };
          
          setClusterData(processedData);
        }
      } catch (err) {
        console.error('Failed to fetch cluster data:', err);
      }
    };

    fetchClusterData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() === '') return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };
    
    setMessages([...messages, newMessage]);
    setInputValue('');
    setLoading(true);
    
    try {
      const response = await fetch('/api/my/v1/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputValue
        })
      });
      
      const data = await response.json();
      console.log('AI Chat response:', data);
      
      if (data.error) {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `Error: ${data.error}\n\nMessage: ${data.message || 'Unknown error'}`,
          sender: 'assistant',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
      } else {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response || "I received your request but couldn't provide a meaningful answer.",
          sender: 'assistant',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Network error: ${error instanceof Error ? error.message : String(error)}`,
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kubernetes Chat Assistant</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-start space-x-2">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm">AI</div>
            <div className="bg-muted p-3 rounded-lg">
              <p>Hello! I'm your Kubernetes assistant. How can I help you with your cluster?</p>
            </div>
          </div>
          
          <div className="h-64 overflow-y-auto space-y-3">
            {messages.map((message) => (
              <div 
                key={message.id} 
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} space-x-2`}
              >
                {message.sender === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm">AI</div>
                )}
                <div className={`p-3 rounded-lg max-w-xs ${message.sender === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                  <p>{message.content}</p>
                </div>
                {message.sender === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-white text-sm">U</div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex justify-start space-x-2">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm">AI</div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input 
              placeholder="Ask about your cluster..." 
              className="flex-1"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
            <Button type="submit" disabled={loading}>Send</Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatInterface;
