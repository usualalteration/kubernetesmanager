import { useState } from "react";
import { NavLink } from "@/components/NavLink";
import { Button } from "@/components/ui/button";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import PodMonitor from "@/components/dashboard/PodMonitor";
import PvcMonitor from "@/components/dashboard/PvcMonitor";
import NodeMonitor from "@/components/dashboard/NodeMonitor";
import ChatInterface from "@/components/dashboard/ChatInterface";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("pods");
  const [kubeconfigFile, setKubeconfigFile] = useState<File | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
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
            <span className="text-sm text-muted-foreground">Kubernetes Dashboard</span>
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
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b">
        <div className="container flex items-center space-x-4 px-4 py-2">
          <NavLink 
            to="/dashboard" 
            className="text-sm font-medium transition-colors hover:text-primary"
            activeClassName="text-primary"
          >
            Dashboard
          </NavLink>
          <NavLink 
            to="/dashboard/pods" 
            className="text-sm font-medium transition-colors hover:text-primary"
            activeClassName="text-primary"
          >
            Pods
          </NavLink>
          <NavLink 
            to="/dashboard/pvcs" 
            className="text-sm font-medium transition-colors hover:text-primary"
            activeClassName="text-primary"
          >
            PVCs
          </NavLink>
          <NavLink 
            to="/dashboard/nodes" 
            className="text-sm font-medium transition-colors hover:text-primary"
            activeClassName="text-primary"
          >
            Nodes
          </NavLink>
          <NavLink 
            to="/dashboard/chat" 
            className="text-sm font-medium transition-colors hover:text-primary"
            activeClassName="text-primary"
          >
            Chat
          </NavLink>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="pods">Pods</TabsTrigger>
            <TabsTrigger value="pvcs">PVCs</TabsTrigger>
            <TabsTrigger value="nodes">Nodes</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
          </TabsList>

          {/* Pods Tab */}
          <TabsContent value="pods">
            <PodMonitor />
          </TabsContent>

          {/* PVCs Tab */}
          <TabsContent value="pvcs">
            <PvcMonitor />
          </TabsContent>

          {/* Nodes Tab */}
          <TabsContent value="nodes">
            <NodeMonitor />
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <ChatInterface />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Dashboard;
