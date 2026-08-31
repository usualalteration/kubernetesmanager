import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { NavLink } from "@/components/NavLink";
import { useKubeconfig } from "@/hooks/use-kubeconfig";

const Header = () => {
  const { loading, configured, activeInfo } = useKubeconfig();

  return (
    <header className="border-b">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-2">
          <h1 className="text-xl font-bold">Truk8s</h1>
          <Badge variant="secondary">Kubernetes Dashboard</Badge>
        </div>
        <div className="flex items-center space-x-4">
          {/* Kubeconfig status indicator */}
          {loading ? (
            <Badge variant="outline" className="text-muted-foreground">
              <span className="mr-1 inline-block h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
              Checking…
            </Badge>
          ) : configured ? (
            <Badge variant="default" className="bg-green-600 hover:bg-green-600">
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-white" />
              {activeInfo?.current_context || "Connected"}
            </Badge>
          ) : (
            <Badge variant="destructive">
              <span className="mr-1 inline-block h-2 w-2 rounded-full bg-white" />
              No kubeconfig
            </Badge>
          )}

          <NavLink to="/">
            <Button variant="ghost">Home</Button>
          </NavLink>
          <NavLink to="/pods">
            <Button variant="ghost" disabled={!configured}>
              Pods
            </Button>
          </NavLink>
          <NavLink to="/pvcs">
            <Button variant="ghost" disabled={!configured}>
              PVCs
            </Button>
          </NavLink>
          <NavLink to="/nodes">
            <Button variant="ghost" disabled={!configured}>
              Nodes
            </Button>
          </NavLink>
          <NavLink to="/chat">
            <Button variant="ghost" disabled={!configured}>
              Chat
            </Button>
          </NavLink>
        </div>
      </div>
    </header>
  );
};

export default Header;
