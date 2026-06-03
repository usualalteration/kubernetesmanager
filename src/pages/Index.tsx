import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NavLink } from "@/components/NavLink";
import { Badge } from "@/components/ui/badge";

const Index = () => {
  const features = [
    {
      title: "Pod Monitor",
      description: "Monitora lo stato dei pod, visualizza i log e filtra per namespace",
      icon: "📦",
    },
    {
      title: "PVC Monitor",
      description: "Gestisci Persistent Volume Claims e monitora l'utilizzo dello storage",
      icon: "💾",
    },
    {
      title: "Node Monitor",
      description: "Visualizza lo stato dei nodi, CPU, memoria e capacità del cluster",
      icon: "🖥️",
    },
    {
      title: "AI Chat",
      description: "Fai domande al cluster usando linguaggio naturale e ottieni risposte basate sui dati",
      icon: "💬",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold">Truk8s</h1>
              <Badge variant="secondary">Kubernetes Dashboard</Badge>
            </div>
            <NavLink to="/dashboard">
              <Button>Go to Dashboard</Button>
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

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="text-4xl mb-2">{feature.icon}</div>
                <CardTitle>{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <NavLink to="/dashboard">
                  <Button variant="outline" className="w-full">
                    View Details
                  </Button>
                </NavLink>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Info Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">
            Powered by Trustable
          </p>
          <p className="text-xs text-muted-foreground/70 max-w-lg mx-auto">
            Supporto completo per AI, database (SQL, NoSQL, vector), Redis e S3 con backend serverless nelle prossime release
          </p>
        </div>
      </section>
    </div>
  );
};

export default Index;
