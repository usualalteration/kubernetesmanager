import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import PvcMonitor from "@/components/dashboard/PvcMonitor";
import Header from "@/components/Header";
import { NavLink } from "@/components/NavLink";

const Pvcs = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold mb-2">PVCs</h2>
            <p className="text-muted-foreground">Monitor Persistent Volume Claims</p>
          </div>
          <NavLink to="/">
            <Button variant="outline">
              ← Home
            </Button>
          </NavLink>
        </div>

        <Card>
          <CardContent>
            <PvcMonitor />
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Pvcs;
