import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import NodeMonitor from "@/components/dashboard/NodeMonitor";
import { NavLink } from "@/components/NavLink";

const Nodes = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
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
            <NavLink to="/chat">
              <Button variant="ghost">Chat</Button>
            </NavLink>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <NodeMonitor />
      </main>
    </div>
  );
};

export default Nodes;
