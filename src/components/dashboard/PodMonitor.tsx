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
  const [pods, setPods] = useState<Pod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPods = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/my/v1/cluster-monitor');
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
        } else {
          // Process pods data to match expected format
          const processedPods: Pod[] = data.pods.items.map((pod: any) => ({
            id: pod.name,
            name: pod.name,
            namespace: pod.namespace || 'default',
            status: pod.status || 'Unknown',
            restarts: 0, // We don't have restarts data in the API yet
            age: 'N/A', // We don't have age data in the API yet
            node: pod.node || 'N/A'
          }));
          
          setPods(processedPods);
        }
      } catch (err) {
        setError('Failed to fetch pods data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPods();
  }, []);

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

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pod Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p>Loading pods data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pod Monitoring</CardTitle>
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
