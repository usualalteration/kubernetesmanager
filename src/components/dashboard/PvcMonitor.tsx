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
  // Mock data for PVCs
  const pvcs: Pvc[] = [
    {
      id: "pvc-1",
      name: "data-pvc",
      namespace: "default",
      status: "Bound",
      capacity: "20Gi",
      used: "10Gi",
      storageClass: "standard",
      age: "2d"
    },
    {
      id: "pvc-2",
      name: "logs-pvc",
      namespace: "kube-system",
      status: "Bound",
      capacity: "15Gi",
      used: "5Gi",
      storageClass: "standard",
      age: "1w"
    },
    {
      id: "pvc-3",
      name: "database-pvc",
      namespace: "production",
      status: "Bound",
      capacity: "100Gi",
      used: "85Gi",
      storageClass: "fast",
      age: "3w"
    },
    {
      id: "pvc-4",
      name: "temp-pvc",
      namespace: "temp",
      status: "Pending",
      capacity: "5Gi",
      used: "0Gi",
      storageClass: "standard",
      age: "1h"
    },
    {
      id: "pvc-5",
      name: "backup-pvc",
      namespace: "backup",
      status: "Lost",
      capacity: "50Gi",
      used: "40Gi",
      storageClass: "standard",
      age: "1m"
    },
  ];

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
