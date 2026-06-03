import { useState, useEffect } from "react";
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
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNodes = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/my/v1/cluster-monitor');
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
        } else {
          // Process nodes data to match expected format
          const processedNodes: Node[] = data.nodes.items.map((node: any) => ({
            id: node.name,
            name: node.name,
            status: node.status || 'Unknown',
            role: node.labels && node.labels['node-role.kubernetes.io/control-plane'] ? 'master' : 'worker',
            cpu: 'N/A', // We don't have cpu data in the API yet
            memory: 'N/A', // We don't have memory data in the API yet
            pods: 0, // We don't have pod count data in the API yet
            age: 'N/A' // We don't have age data in the API yet
          }));
          
          setNodes(processedNodes);
        }
      } catch (err) {
        setError('Failed to fetch nodes data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchNodes();
  }, []);

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

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Node Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p>Loading nodes data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Node Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p className="text-red-500">Error: {error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

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
