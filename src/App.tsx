import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { KubeconfigProvider, useKubeconfig } from "@/hooks/use-kubeconfig";
import Home from "./pages/Home";
import Pods from "./pages/Pods";
import Pvcs from "./pages/Pvcs";
import Nodes from "./pages/Nodes";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard/Index";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { loading, configured } = useKubeconfig();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Checking kubeconfig…</p>
      </div>
    );
  }
  if (!configured) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <KubeconfigProvider>
        <HashRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route
              path="/pods"
              element={
                <ProtectedRoute>
                  <Pods />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pvcs"
              element={
                <ProtectedRoute>
                  <Pvcs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/nodes"
              element={
                <ProtectedRoute>
                  <Nodes />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <Chat />
                </ProtectedRoute>
              }
            />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dashboard/*" element={<Dashboard />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </HashRouter>
      </KubeconfigProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
