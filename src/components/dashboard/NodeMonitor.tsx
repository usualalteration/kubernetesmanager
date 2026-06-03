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

interface Node {
  id: string;
  name: string;
  status: 'Ready' | 'NotReady' | 'SchedulingDisabled';
  role: string;
  cpu: string;
  memory: string;
  pods: number;
  age: string;
}

const NodeMonitor = () => {
  // Mock data for nodes
  const nodes: Node[] = [
    {
      id: "node-1",
      name: "node-01",
      status: "Ready",
      role: "master",
      cpu: "2000m",
      memory: "7800Mi",
      pods: 15,
      age: "2w"
    },
    {
      id: "node-2",
      name: "node-02",
      status: "Ready",
      role: "worker",
      cpu: "4000m",
      memory: "15600Mi",
      pods: 25,
      age: "1w"
    },
    {
      id: "node-3",
      name: "node-03",
      status: "NotReady",
      role: "worker",
      cpu: "0m",
      memory: "0Mi",
      pods: 0,
      age: "3d"
    },
    {
      id: "node-4",
      name: "node-04",
      status: "Ready",
      role: "worker",
      cpu: "3000m",
      memory: "11700Mi",
      pods: 20,
      age: "3w"
    },
    {
      id: "node-5",
      name: "node-05",
      status: "SchedulingDisabled",
      role: "worker",
      cpu: "1500m",
      memory: "3900Mi",
      pods: 10,
      age: "1m"
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Ready':
        return 'bg-green-100 text-green-800';
      case 'NotReady':
        return 'bg-red-100 text-red-800';
      case 'SchedulingDisabled':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Node Monitoring</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-lg font-semibold">Cluster Nodes</h3>
            <p className="text-sm text-muted-foreground">
              Total nodes: {nodes.length} | Ready: {nodes.filter(n => n.status === 'Ready').length}
            </p>
          </div>
          <div className="flex space-x-2">
            <select className="rounded-md border bg-background px-3 py-1 text-sm">
              <option>All Nodes</option>
              <option>Ready</option>
              <option>NotReady</option>
              <option>SchedulingDisabled</option>
            </select>
            <input 
              type="text" 
              placeholder="Search nodes..." 
              className="rounded-md border bg-background px-3 py-1 text-sm"
            />
          </div>
        </div>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>CPU</TableHead>
                <TableHead>Memory</TableHead>
                <TableHead>Pods</TableHead>
                <TableHead>Age</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {nodes.map((node) => (
                <TableRow key={node.id}>
                  <TableCell className="font-medium">{node.name}</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(node.status)}>{node.status}</Badge>
                  </TableCell>
                  <TableCell>{node.role}</TableCell>
                  <TableCell>{node.cpu}</TableCell>
                  <TableCell>{node.memory}</TableCell>
                  <TableCell>{node.pods}</TableCell>
                  <TableCell>{node.age}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default NodeMonitor;
