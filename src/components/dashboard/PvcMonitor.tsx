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

interface Pvc {
  id: string;
  name: string;
  namespace: string;
  status: 'Bound' | 'Pending' | 'Lost';
  capacity: string;
  used: string;
  storageClass: string;
  age: string;
}

const PvcMonitor = () => {
  const [pvcs, setPvcs] = useState<Pvc[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPvcs = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/my/v1/cluster-monitor');
        const data = await response.json();
        
        if (data.error) {
          setError(data.error);
        } else {
          // Process PVCs data to match expected format
          const processedPvcs: Pvc[] = data.pvcs.items.map((pvc: any) => ({
            id: pvc.name,
            name: pvc.name,
            namespace: pvc.namespace || 'default',
            status: pvc.status || 'Unknown',
            capacity: pvc.capacity || 'N/A',
            used: 'N/A', // We don't have used data in the API yet
            storageClass: pvc.storageClass || 'N/A',
            age: 'N/A' // We don't have age data in the API yet
          }));
          
          setPvcs(processedPvcs);
        }
      } catch (err) {
        setError('Failed to fetch PVCs data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPvcs();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Bound':
        return 'bg-green-100 text-green-800';
      case 'Pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'Lost':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PVC Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <p>Loading PVCs data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>PVC Monitoring</CardTitle>
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
        <CardTitle>PVC Monitoring</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-lg font-semibold">Persistent Volume Claims</h3>
            <p className="text-sm text-muted-foreground">
              Total PVCs: {pvcs.length} | Bound: {pvcs.filter(p => p.status === 'Bound').length}
            </p>
          </div>
          <div className="flex space-x-2">
            <select className="rounded-md border bg-background px-3 py-1 text-sm">
              <option>All Namespaces</option>
              <option>default</option>
              <option>kube-system</option>
              <option>production</option>
              <option>temp</option>
              <option>backup</option>
            </select>
            <input 
              type="text" 
              placeholder="Search PVCs..." 
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
                <TableHead>Capacity</TableHead>
                <TableHead>Used</TableHead>
                <TableHead>Storage Class</TableHead>
                <TableHead>Age</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pvcs.map((pvc) => (
                <TableRow key={pvc.id}>
                  <TableCell className="font-medium">{pvc.name}</TableCell>
                  <TableCell>{pvc.namespace}</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(pvc.status)}>{pvc.status}</Badge>
                  </TableCell>
                  <TableCell>{pvc.capacity}</TableCell>
                  <TableCell>{pvc.used}</TableCell>
                  <TableCell>{pvc.storageClass}</TableCell>
                  <TableCell>{pvc.age}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default PvcMonitor;
