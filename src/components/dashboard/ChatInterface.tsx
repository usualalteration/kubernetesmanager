import { useState } from "react";
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

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your Kubernetes assistant. How can I help you with your cluster?',
      sender: 'assistant',
      timestamp: new Date(),
    },
    {
      id: '2',
      content: 'Can you tell me about the status of pods in the default namespace?',
      sender: 'user',
      timestamp: new Date(),
    },
    {
      id: '3',
      content: 'There are 12 pods in the default namespace. 10 are running, 1 is pending, and 1 is failed.',
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);
  
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
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
    
    // Simulate AI response after a delay
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: 'I\'ve analyzed your request. Based on the cluster data, I can provide detailed insights about your Kubernetes resources. Would you like me to generate a report?',
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
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
          </div>
          
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input 
              placeholder="Ask about your cluster..." 
              className="flex-1"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
            />
            <Button type="submit">Send</Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatInterface;
