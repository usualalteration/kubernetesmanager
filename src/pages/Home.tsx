import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NavLink } from "@/components/NavLink";
import { Badge } from "@/components/ui/badge";

const Home = () => {
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
            <NavLink to="/pods">
              <Button variant="ghost">Pods</Button>
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

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center space-y-4">
          <h2 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Kubernetes Cluster Management
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Visualizza, monitora e gestisci il tuo cluster Kubernetes con un'interfaccia intuitiva e potente.
          </p>
        </div>
      </section>

      {/* Quick Access Grid */}
      <section className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="text-4xl mb-2">📦</div>
              <CardTitle>Pods</CardTitle>
              <CardDescription>Monitora i pod del cluster</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/pods">
                <Button variant="outline" className="w-full">
                  View Pods
                </Button>
              </NavLink>
            </CardContent>
          </Card>
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="text-4xl mb-2">💾</div>
              <CardTitle>PVCs</CardTitle>
              <CardDescription>Storage e volume claims</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/pvcs">
                <Button variant="outline" className="w-full">
                  View PVCs
                </Button>
              </NavLink>
            </CardContent>
          </Card>
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="text-4xl mb-2">🖥️</div>
              <CardTitle>Nodes</CardTitle>
              <CardDescription>Nodi e risorse</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/nodes">
                <Button variant="outline" className="w-full">
                  View Nodes
                </Button>
              </NavLink>
            </CardContent>
          </Card>
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="text-4xl mb-2">💬</div>
              <CardTitle>Chat</CardTitle>
              <CardDescription>AI Assistant</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/chat">
                <Button variant="outline" className="w-full">
                  Start Chat
                </Button>
              </NavLink>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Info Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">
            Powered by Trustable
          </p>
        </div>
      </section>
    </div>
  );
};

export default Home;
