import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import NodeMonitor from "@/components/dashboard/NodeMonitor";
import Header from "@/components/Header";

const Nodes = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <NodeMonitor />
      </main>
    </div>
  );
};

export default Nodes;
