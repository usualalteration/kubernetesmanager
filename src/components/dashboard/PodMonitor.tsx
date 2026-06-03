import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";

interface Pod {
  id: string;
  name: string;
  namespace: string;
  status: 'Running' | 'Pending' | 'Failed' | 'Succeeded';
  restarts: number;
  age: string;
  node: string;
}

const PodMonitor = () => {
  // Mock data for pods
  const pods: Pod[] = [
    {
      id: "pod-1",
      name: "web-app-6d5f8c7b9-xyz12",
      namespace: "default",
      status: "Running",
      restarts: 0,
      age: "2d",
      node: "node-01"
    },
    {
      id: "pod-2",
      name: "api-server-7b8c9d0e1-abc23",
      namespace: "kube-system",
      status: "Pending",
      restarts: 1,
      age: "1h",
      node: "node-02"
    },
    {
      id: "pod-3",
      name: "db-mysql-5d6e7f8c9-def34",
      namespace: "production",
      status: "Failed",
      restarts: 5,
      age: "3d",
      node: "node-01"
    },
    {
      id: "pod-4",
      name: "cache-redis-9a8b7c6d5-efg56",
      namespace: "default",
      status: "Running",
      restarts: 0,
      age: "5d",
      node: "node-03"
    },
    {
      id: "pod-5",
      name: "monitoring-agent-123456789-xyz01",
      namespace: "monitoring",
      status: "Running",
      restarts: 2,
      age: "1w",
      node: "node-01"
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Running':
        return 'bg-green-100 text-green-800';
      case 'Pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'Failed':
        return 'bg-red-100 text-red-800';
      case 'Succeeded':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pod Monitoring</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-lg font-semibold">Pods Overview</h3>
            <p className="text-sm text-muted-foreground">
              Total pods: {pods.length} | Running: {pods.filter(p => p.status === 'Running').length} | 
              Pending: {pods.filter(p => p.status === 'Pending').length} | 
              Failed: {pods.filter(p => p.status === 'Failed').length}
            </p>
          </div>
          <div className="flex space-x-2">
            <select className="rounded-md border bg-background px-3 py-1 text-sm">
              <option>All Namespaces</option>
              <option>default</option>
              <option>kube-system</option>
              <option>production</option>
              <option>monitoring</option>
            </select>
            <input 
              type="text" 
              placeholder="Search pods..." 
              className="rounded-md border bg-background px-3 py-1 text-sm"
            />
          </div>
        </div>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Namespace</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Node</TableHead>
                <TableHead>Restarts</TableHead>
                <TableHead>Age</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pods.map((pod) => (
                <TableRow key={pod.id}>
                  <TableCell className="font-medium">{pod.name}</TableCell>
                  <TableCell>{pod.namespace}</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(pod.status)}>{pod.status}</Badge>
                  </TableCell>
                  <TableCell>{pod.node}</TableCell>
                  <TableCell>{pod.restarts}</TableCell>
                  <TableCell>{pod.age}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default PodMonitor;
