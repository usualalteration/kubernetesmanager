import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import PodMonitor from "@/components/dashboard/PodMonitor";
import { NavLink } from "@/components/NavLink";

const Pods = () => {
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
            <NavLink to="/pvcs">
              <Button variant="ghost">PVCs</Button>
            </NavLink>
            <NavLink to="/nodes">
              <Button variant="ghost">Nodes</Button>
            </NavLink>
            <NavLink to="/chat">
              <Button variant="ghost">Chat</Button>
            </NavLink>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold mb-2">Pods</h2>
            <p className="text-muted-foreground">Monitora i pod del cluster Kubernetes</p>
          </div>
          <NavLink to="/">
            <Button variant="outline">
              ← Home
            </Button>
          </NavLink>
        </div>

        <Card>
          <CardContent>
            <PodMonitor />
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Pods;
