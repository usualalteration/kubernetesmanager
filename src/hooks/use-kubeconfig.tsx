import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

interface KubeconfigItem {
  key: string;
  filename: string;
  uploaded_at: string;
  size: number;
  active: boolean;
}

interface KubeconfigInfo {
  filename?: string;
  clusters?: number;
  contexts?: number;
  users?: number;
  current_context?: string;
}

interface KubeconfigStatusValue {
  loading: boolean;
  configured: boolean;
  error: string;
  items: KubeconfigItem[];
  activeInfo: KubeconfigInfo | null;
  refresh: () => void;
  deleteConfig: (key: string) => Promise<boolean>;
  setActive: (key: string) => Promise<boolean>;
}

const KubeconfigContext = createContext<KubeconfigStatusValue>({
  loading: true,
  configured: false,
  error: "",
  items: [],
  activeInfo: null,
  refresh: () => {},
  deleteConfig: async () => false,
  setActive: async () => false,
});

const normalize = (raw: any) =>
  raw && typeof raw === "object" && "body" in raw ? raw.body : raw;

export const KubeconfigProvider = ({ children }: { children: ReactNode }) => {
  const [loading, setLoading] = useState(true);
  const [configured, setConfigured] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState<KubeconfigItem[]>([]);
  const [activeInfo, setActiveInfo] = useState<KubeconfigInfo | null>(null);

  const checkStatus = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/my/v1/kubeconfig-status");
      const data = normalize(await response.json());
      if (data?.ok) {
        setConfigured(!!data.configured);
        setError(data.error || "");
        setItems(data.items || []);
        if (data.active_info) {
          setActiveInfo({
            filename: data.active_info.filename,
            clusters: data.active_info.clusters,
            contexts: data.active_info.contexts,
            users: data.active_info.users,
            current_context: data.active_info.current_context,
          });
        } else {
          setActiveInfo(null);
        }
      } else {
        setConfigured(false);
        setError(data?.error || "Failed to check kubeconfig status");
        setItems([]);
        setActiveInfo(null);
      }
    } catch (err) {
      setConfigured(false);
      setError(err instanceof Error ? err.message : "Network error");
      setItems([]);
      setActiveInfo(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  const deleteConfig = useCallback(
    async (key: string): Promise<boolean> => {
      try {
        const response = await fetch("/api/my/v1/kubeconfig-status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "delete", key }),
        });
        const data = normalize(await response.json());
        if (data?.ok) {
          await checkStatus();
          return true;
        }
        return false;
      } catch {
        return false;
      }
    },
    [checkStatus]
  );

  const setActive = useCallback(
    async (key: string): Promise<boolean> => {
      try {
        const response = await fetch("/api/my/v1/kubeconfig-status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: "set-active", key }),
        });
        const data = normalize(await response.json());
        if (data?.ok) {
          await checkStatus();
          return true;
        }
        return false;
      } catch {
        return false;
      }
    },
    [checkStatus]
  );

  return (
    <KubeconfigContext.Provider
      value={{
        loading,
        configured,
        error,
        items,
        activeInfo,
        refresh: checkStatus,
        deleteConfig,
        setActive,
      }}
    >
      {children}
    </KubeconfigContext.Provider>
  );
};

export const useKubeconfig = () => useContext(KubeconfigContext);
