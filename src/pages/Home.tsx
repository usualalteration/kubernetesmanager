import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NavLink } from "@/components/NavLink";
import Header from "@/components/Header";
import { useKubeconfig } from "@/hooks/use-kubeconfig";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const Home = () => {
  const { configured, activeInfo, items, refresh, deleteConfig, setActive } =
    useKubeconfig();
  const [kubeconfigFile, setKubeconfigFile] = useState<File | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingKey, setDeletingKey] = useState<string | null>(null);

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        const base64 = result?.split(",")[1];
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

        const response = await fetch("/api/my/v1/upload-kubeconfig", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            file_data: base64Data,
            file_name: file.name,
          }),
        });

        const result = await response.json();

        if (result.valid) {
          toast.success(`Kubeconfig "${file.name}" uploaded successfully!`);
          setIsDialogOpen(false);
          setKubeconfigFile(null);
          refresh();
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

  const handleDelete = async (key: string, filename: string) => {
    setDeletingKey(key);
    const ok = await deleteConfig(key);
    setDeletingKey(null);
    if (ok) {
      toast.success(`Kubeconfig "${filename}" removed`);
    } else {
      toast.error(`Error removing "${filename}"`);
    }
  };

  const handleSetActive = async (key: string, filename: string) => {
    const ok = await setActive(key);
    if (ok) {
      toast.success(`"${filename}" set as the active kubeconfig`);
    } else {
      toast.error(`Error activating "${filename}"`);
    }
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString("en-US", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Kubeconfig status banner */}
      {!configured && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border-b border-amber-200 dark:border-amber-900">
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-amber-600 dark:text-amber-400">⚠️</span>
              <p className="text-sm text-amber-800 dark:text-amber-200">
                No kubeconfig uploaded. Upload a kubeconfig file to access
                cluster features.
              </p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">Upload Kubeconfig</Button>
              </DialogTrigger>
              <UploadDialog
                kubeconfigFile={kubeconfigFile}
                isUploading={isUploading}
                onFileChange={handleFileUpload}
              />
            </Dialog>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="text-center space-y-4">
          <h2 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Kubernetes Cluster Management
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            View, monitor and manage your Kubernetes cluster with an
            intuitive and powerful interface.
          </p>
          {configured && activeInfo && (
            <div className="inline-flex items-center gap-2 rounded-lg bg-green-50 dark:bg-green-950/30 px-4 py-2 border border-green-200 dark:border-green-900">
              <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              <span className="text-sm text-green-800 dark:text-green-200">
                Connected cluster:{" "}
                <strong>{activeInfo.current_context || "default"}</strong>
                {" "}({activeInfo.clusters} cluster
                {activeInfo.clusters !== 1 ? "s" : ""},{" "}
                {activeInfo.contexts} context
                {activeInfo.contexts !== 1 ? "s" : ""})
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Kubeconfig management section */}
      <section className="container mx-auto px-4 py-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Kubeconfig</CardTitle>
                <CardDescription>
                  Manage cluster kubeconfig files
                </CardDescription>
              </div>
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">+ Add</Button>
                </DialogTrigger>
                <UploadDialog
                  kubeconfigFile={kubeconfigFile}
                  isUploading={isUploading}
                  onFileChange={handleFileUpload}
                />
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No kubeconfig uploaded. Click "Add" to upload one.
              </p>
            ) : (
              <div className="space-y-2">
                {items.map((item) => (
                  <div
                    key={item.key}
                    className={`flex items-center justify-between rounded-lg border p-3 ${
                      item.active
                        ? "border-green-300 bg-green-50 dark:bg-green-950/20 dark:border-green-800"
                        : "border-border"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <span className="text-2xl">📄</span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium truncate">
                            {item.filename}
                          </p>
                          {item.active && (
                            <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-green-600 px-2 py-0.5 text-xs font-medium text-white">
                              <span className="inline-block h-1.5 w-1.5 rounded-full bg-white" />
                              Active
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(item.uploaded_at)}
                          {" · "}
                          {(item.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {!item.active && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleSetActive(item.key, item.filename)
                          }
                        >
                          Set Active
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={deletingKey === item.key}
                        onClick={() =>
                          handleDelete(item.key, item.filename)
                        }
                      >
                        {deletingKey === item.key ? "…" : "Delete"}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>

      {/* Quick Access Grid */}
      <section className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className={configured ? "hover:shadow-lg transition-shadow" : "opacity-50"}>
            <CardHeader>
              <div className="text-4xl mb-2">📦</div>
              <CardTitle>Pods</CardTitle>
              <CardDescription>Monitor cluster pods</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/pods">
                <Button variant="outline" className="w-full" disabled={!configured}>
                  View Pods
                </Button>
              </NavLink>
            </CardContent>
          </Card>
          <Card className={configured ? "hover:shadow-lg transition-shadow" : "opacity-50"}>
            <CardHeader>
              <div className="text-4xl mb-2">💾</div>
              <CardTitle>PVCs</CardTitle>
              <CardDescription>Storage and volume claims</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/pvcs">
                <Button variant="outline" className="w-full" disabled={!configured}>
                  View PVCs
                </Button>
              </NavLink>
            </CardContent>
          </Card>
          <Card className={configured ? "hover:shadow-lg transition-shadow" : "opacity-50"}>
            <CardHeader>
              <div className="text-4xl mb-2">🖥️</div>
              <CardTitle>Nodes</CardTitle>
              <CardDescription>Nodes and resources</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/nodes">
                <Button variant="outline" className="w-full" disabled={!configured}>
                  View Nodes
                </Button>
              </NavLink>
            </CardContent>
          </Card>
          <Card className={configured ? "hover:shadow-lg transition-shadow" : "opacity-50"}>
            <CardHeader>
              <div className="text-4xl mb-2">💬</div>
              <CardTitle>Chat</CardTitle>
              <CardDescription>AI Assistant</CardDescription>
            </CardHeader>
            <CardContent>
              <NavLink to="/chat">
                <Button variant="outline" className="w-full" disabled={!configured}>
                  Start Chat
                </Button>
              </NavLink>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Info Section */}
      <section className="container mx-auto px-4 py-8">
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">Powered by Trustable</p>
        </div>
      </section>
    </div>
  );
};

// Upload dialog component
const UploadDialog = ({
  kubeconfigFile,
  isUploading,
  onFileChange,
}: {
  kubeconfigFile: File | null;
  isUploading: boolean;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) => (
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Upload Kubeconfig File</DialogTitle>
      <DialogDescription>
        Upload a kubeconfig file to connect to your Kubernetes cluster.
      </DialogDescription>
    </DialogHeader>
    <div className="grid gap-4 py-4">
      <p className="text-sm text-muted-foreground">
        Supported formats: YAML (.yaml, .yml), JSON (.json), TXT and files
        without an extension. The file will be validated as a valid Kubernetes
        kubeconfig and set as the active configuration.
      </p>
      {kubeconfigFile && (
        <div className="flex items-center gap-2 rounded-md bg-muted p-2">
          <span className="text-sm font-medium">Selected file:</span>
          <span className="text-sm text-muted-foreground">
            {kubeconfigFile.name}
          </span>
        </div>
      )}
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="kubeconfig" className="text-right">
          File
        </Label>
        <Input
          id="kubeconfig"
          name="kubeconfig"
          type="file"
          className="col-span-3"
          onChange={onFileChange}
          disabled={isUploading}
        />
      </div>
    </div>
    {kubeconfigFile && (
      <div className="text-sm text-muted-foreground">
        <p>
          File: <span className="font-medium">{kubeconfigFile.name}</span>
        </p>
        <p>Size: {(kubeconfigFile.size / 1024).toFixed(2)} KB</p>
      </div>
    )}
  </DialogContent>
);

export default Home;
