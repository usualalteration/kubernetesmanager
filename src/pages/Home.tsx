import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NavLink } from "@/components/NavLink";
import { Badge } from "@/components/ui/badge";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const Home = () => {
  const [kubeconfigFile, setKubeconfigFile] = useState<File | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        const base64 = result?.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setKubeconfigFile(file);
      
      try {
        setIsUploading(true);
        const base64Data = await fileToBase64(file);
        
        const response = await fetch('/api/my/v1/upload-kubeconfig', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            file_data: base64Data,
            file_name: file.name
          })
        });
        
        const result = await response.json();
        
        if (result.valid) {
          toast.success(`Kubeconfig "${file.name}" caricato con successo!`);
          setIsDialogOpen(false);
        } else {
          toast.error(result.error || "Errore nel file kubeconfig");
        }
      } catch (error) {
        toast.error("Errore durante il caricamento del file");
        console.error(error);
      } finally {
        setIsUploading(false);
      }
    }
  };
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
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">Upload Kubeconfig</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Upload Kubeconfig File</DialogTitle>
                  <DialogDescription>
                    Please upload your kubeconfig file to connect to your Kubernetes cluster.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  {kubeconfigFile && (
                    <div className="flex items-center gap-2 rounded-md bg-muted p-2">
                      <span className="text-sm font-medium">File selezionato:</span>
                      <span className="text-sm text-muted-foreground">{kubeconfigFile.name}</span>
                    </div>
                  )}
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="kubeconfig" className="text-right">
                      File
                    </Label>
                    <Input
                      id="kubeconfig"
                      type="file"
                      className="col-span-3"
                      accept=".yaml,.yml"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                    />
                  </div>
                </div>
                {kubeconfigFile && (
                  <div className="text-sm text-muted-foreground">
                    <p>File: <span className="font-medium">{kubeconfigFile.name}</span></p>
                    <p>Dimensione: {(kubeconfigFile.size / 1024).toFixed(2)} KB</p>
                  </div>
                )}
              </DialogContent>
            </Dialog>
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
