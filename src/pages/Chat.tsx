import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ChatInterface from "@/components/dashboard/ChatInterface";
import { NavLink } from "@/components/NavLink";

const Chat = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b shrink-0">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold">Truk8s</h1>
            <Badge variant="secondary">Kubernetes Dashboard</Badge>
          </div>
          <div className="flex items-center space-x-4">
            <NavLink to="/">
              <Button variant="ghost">Home</Button>
            </NavLink>
            <NavLink to="/pods">
              <Button variant="ghost">Pods</Button>
            </NavLink>
            <NavLink to="/pvcs">
              <Button variant="ghost">PVCs</Button>
            </NavLink>
            <NavLink to="/nodes">
              <Button variant="ghost">Nodes</Button>
            </NavLink>
          </div>
        </div>
      </header>

      {/* Chat Interface - full height below header */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface />
      </div>
    </div>
  );
};

export default Chat;
