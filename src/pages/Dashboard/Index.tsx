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
      reader.onload = (e) => {
        const result = e.target?.result as string;
        // Remove data URL prefix (e.g., "data:text/plain;base64,")
        const base64 = result?.split(',')[1];
        console.log("Base64 length:", base64?.length);
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
        console.log("Base64 data length:", base64Data?.length);
        console.log("Base64 data first 50 chars:", base64Data?.substring(0, 50));
        
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
        alert("Result: " + JSON.stringify(result, null, 2));
        console.log("Kubeconfig validation result:", result);
        console.log("File name:", file.name);
        console.log("File size:", file.size);
        
        if (result.valid) {
          toast.success(`Kubeconfig "${file.name}" uploaded successfully!`);
          setIsDialogOpen(false);
        } else {
          toast.error(result.error || "Error in kubeconfig file");
        }
      } catch (error) {
        toast.error("Error while uploading the file");
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
                  <p className="text-sm text-muted-foreground">
                    Supported formats: YAML (.yaml, .yml), JSON (.json), TXT and files
                    without an extension. The file will be validated as a valid
                    Kubernetes kubeconfig.
                  </p>
                  {kubeconfigFile && (
                    <div className="flex items-center gap-2 rounded-md bg-muted p-2">
                      <span className="text-sm font-medium">Selected file:</span>
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
                      onChange={handleFileUpload}
                      disabled={isUploading}
                    />
                  </div>
                </div>
                {kubeconfigFile && (
                  <div className="text-sm text-muted-foreground">
                    <p>File: <span className="font-medium">{kubeconfigFile.name}</span></p>
                    <p>Size: {(kubeconfigFile.size / 1024).toFixed(2)} KB</p>
                  </div>
                )}
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

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
