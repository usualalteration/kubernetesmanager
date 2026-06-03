import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NavLink } from "@/components/NavLink";
import { Badge } from "@/components/ui/badge";
import PodMonitor from "@/components/dashboard/PodMonitor";
import PvcMonitor from "@/components/dashboard/PvcMonitor";
import NodeMonitor from "@/components/dashboard/NodeMonitor";
import ChatInterface from "@/components/dashboard/ChatInterface";
import { useState } from "react";

const Index = () => {
  const [activeTab, setActiveTab] = useState("pods");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold">Truk8s</h1>
            <Badge variant="secondary">Kubernetes Dashboard</Badge>
          </div>
          <NavLink to="/dashboard">
            <Button variant="outline">Dashboard</Button>
          </NavLink>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="text-4xl mb-2">📦</div>
              <CardTitle>Pods</CardTitle>
              <CardDescription>Monitora i pod del cluster</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/dashboard">
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
              <NavLink to="/dashboard">
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
              <NavLink to="/dashboard">
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
              <NavLink to="/dashboard">
                <Button variant="outline" className="w-full">
                  Start Chat
                </Button>
              </NavLink>
            </CardContent>
          </Card>
        </div>

        {/* Quick View Section */}
        <div className="border rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Quick View</h3>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="pods">Pods</TabsTrigger>
              <TabsTrigger value="pvcs">PVCs</TabsTrigger>
              <TabsTrigger value="nodes">Nodes</TabsTrigger>
              <TabsTrigger value="chat">Chat</TabsTrigger>
            </TabsList>

            <TabsContent value="pods" className="mt-4">
              <PodMonitor />
            </TabsContent>

            <TabsContent value="pvcs" className="mt-4">
              <PvcMonitor />
            </TabsContent>

            <TabsContent value="nodes" className="mt-4">
              <NodeMonitor />
            </TabsContent>

            <TabsContent value="chat" className="mt-4">
              <ChatInterface />
            </TabsContent>
          </Tabs>
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
