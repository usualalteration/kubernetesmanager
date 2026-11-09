import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import PodMonitor from "@/components/dashboard/PodMonitor";
import Header from "@/components/Header";
import { NavLink } from "@/components/NavLink";

const Pods = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold mb-2">Pods</h2>
            <p className="text-muted-foreground">Monitor pods in the Kubernetes cluster</p>
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
