using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public class GraphComputeClient : MonoBehaviour
{
    [System.Serializable]
    private class LocalEdge { public string source; public string target; }
    [System.Serializable]
    private class LocalEdgeContainer { public List<LocalEdge> items; }

    [System.Serializable]
    private class LocalNode
    {
        public string node_id;
        public float x; public float y; public float z;
        public int is_fraud_node; public int cluster_label; public string risk_level;
    }
    [System.Serializable]
    private class LocalNodeContainer { public List<LocalNode> items; }

    // Structure reçue depuis la synchronisation Streamlit
    [System.Serializable]
    public class SyncState { public int cluster_id; public int is_fraud; }

    private string edgesUrl = "http://127.0.0.1:8010/api/edges?limit=2000";
    private string nodesUrl = "http://127.0.0.1:8010/api/nodes";
    private string syncUrl = "http://127.0.0.1:8010/api/sync/nodes/state";

    public float graphScale = 2700f;
    public float spreadAmount = 1500f;

    [System.Serializable]
    public struct GPUComputeNode
    {
        public Matrix4x4 nodeMatrix;
        public Vector4 color;
    }

    [Header("Rendu Nœuds (GPU Instancing)")]
    [SerializeField] private Mesh nodeMesh;
    [SerializeField] private Material dotsMaterial;

    [Header("Rendu Liens (Méthode Classique)")]
    [SerializeField] private GameObject linePrefab;

    private List<GPUComputeNode> nodesToRender = new List<GPUComputeNode>();
    private List<LocalNode> originalNodesData = new List<LocalNode>(); // Sauvegarde des types d'API
    private GraphicsBuffer meshPropertiesBuffer;
    private GraphicsBuffer commandBuffer;
    private Bounds renderBounds;
    private bool isDataReady = false;

    void Start()
    {
        StartCoroutine(LoadGraphHighPerformance());
    }

    IEnumerator LoadGraphHighPerformance()
    {
        Dictionary<string, Vector3> nodePositions = new Dictionary<string, Vector3>();
        List<LocalEdge> validEdges = new List<LocalEdge>();
        HashSet<string> requiredNodeIDs = new HashSet<string>();

        // 1. Récupération des Edges
        using (UnityWebRequest edgeRequest = UnityWebRequest.Get(edgesUrl))
        {
            edgeRequest.timeout = 2;
            yield return edgeRequest.SendWebRequest();
            if (edgeRequest.result == UnityWebRequest.Result.Success)
            {
                LocalEdgeContainer edgeData = JsonUtility.FromJson<LocalEdgeContainer>(edgeRequest.downloadHandler.text);
                if (edgeData != null && edgeData.items != null)
                {
                    validEdges = edgeData.items;
                    foreach (LocalEdge edge in validEdges)
                    {
                        requiredNodeIDs.Add(edge.source.Trim());
                        requiredNodeIDs.Add(edge.target.Trim());
                    }
                }
            }
        }

        // 2. Récupération des Nœuds
        int offset = 0; int chunkSize = 5000; bool hasMore = true;
        while (hasMore)
        {
            using (UnityWebRequest nodeRequest = UnityWebRequest.Get($"{nodesUrl}?limit={chunkSize}&offset={offset}"))
            {
                nodeRequest.timeout = 2;
                yield return nodeRequest.SendWebRequest();
                if (nodeRequest.result == UnityWebRequest.Result.Success)
                {
                    LocalNodeContainer nodeData = JsonUtility.FromJson<LocalNodeContainer>(nodeRequest.downloadHandler.text);
                    if (nodeData == null || nodeData.items == null || nodeData.items.Count == 0) break;

                    foreach (LocalNode node in nodeData.items)
                    {
                        string idTrim = node.node_id.Trim();
                        if (requiredNodeIDs.Count == 0 || requiredNodeIDs.Contains(idTrim))
                        {
                            originalNodesData.Add(node); // Sauvegarde pour les filtres dynamiques

                            GPUComputeNode gpuNode = new GPUComputeNode();
                            float posX = node.x * graphScale + Random.Range(-spreadAmount, spreadAmount);
                            float posY = node.y * graphScale + Random.Range(-spreadAmount, spreadAmount);
                            float posZ = node.z * graphScale + Random.Range(-spreadAmount, spreadAmount);
                            Vector3 position = new Vector3(posX, posY, posZ);

                            nodePositions[idTrim] = position;

                            float size = 30f;
                            if (node.is_fraud_node == 1 || node.risk_level == "critique")
                            {
                                gpuNode.color = new Vector4(1f, 0f, 0f, 1f);
                                size = 60f;
                            }
                            else
                            {
                                switch (node.cluster_label)
                                {
                                    case 1: gpuNode.color = new Vector4(0f, 0.5f, 1f, 1f); break;
                                    case 2: gpuNode.color = new Vector4(0.1f, 1f, 0.2f, 1f); break;
                                    default: gpuNode.color = new Vector4(0.8f, 0.8f, 0.8f, 1f); break;
                                }
                            }
                            gpuNode.nodeMatrix = Matrix4x4.TRS(position, Quaternion.identity, new Vector3(size, size, size));
                            nodesToRender.Add(gpuNode);
                        }
                    }
                    if (nodeData.items.Count < chunkSize) hasMore = false;
                    else offset += chunkSize;
                }
                else hasMore = false;
            }
            yield return null;
        }

        // Mode Secours automatique
        if (nodesToRender.Count == 0)
        {
            Debug.LogWarning("⚠️ Serveur API déconnecté. Génération de la simulation.");
            List<Vector3> mockPositions = new List<Vector3>();
            for (int i = 0; i < 60; i++)
            {
                GPUComputeNode mockNode = new GPUComputeNode();
                Vector3 pos = new Vector3(Random.Range(-600f, 600f), Random.Range(-600f, 600f), Random.Range(-600f, 600f));
                mockPositions.Add(pos);
                mockNode.color = (Random.value > 0.85f) ? new Vector4(1f, 0f, 0f, 1f) : new Vector4(0f, 0.6f, 1f, 1f);
                mockNode.nodeMatrix = Matrix4x4.TRS(pos, Quaternion.identity, Vector3.one * Random.Range(25f, 45f));
                nodesToRender.Add(mockNode);
            }

            for (int i = 0; i < mockPositions.Count - 1; i++)
            {
                SpawnLine(mockPositions[i], mockPositions[i + 1]);
            }
        }
        else
        {
            foreach (LocalEdge edge in validEdges)
            {
                string src = edge.source.Trim();
                string tgt = edge.target.Trim();
                if (nodePositions.ContainsKey(src) && nodePositions.ContainsKey(tgt))
                {
                    SpawnLine(nodePositions[src], nodePositions[tgt]);
                }
            }
        }

        InitializeGPUBuffers();

        // 🔗 Lancement de la synchronisation avec Streamlit en tâche de fond
        if (originalNodesData.Count > 0)
        {
            StartCoroutine(CheckStreamlitSync());
        }
    }

    // Polling asynchrone toutes les secondes vers ton API
    IEnumerator CheckStreamlitSync()
    {
        while (true)
        {
            using (UnityWebRequest request = UnityWebRequest.Get(syncUrl))
            {
                request.timeout = 1;
                yield return request.SendWebRequest();
                if (request.result == UnityWebRequest.Result.Success)
                {
                    SyncState state = JsonUtility.FromJson<SyncState>(request.downloadHandler.text);
                    if (state != null)
                    {
                        UpdateGraphVisuals(state.cluster_id, state.is_fraud);
                    }
                }
            }
            yield return new WaitForSeconds(1.0f);
        }
    }

    // Modification dynamique des structures de données et mise à jour du GPU Buffer
    void UpdateGraphVisuals(int targetCluster, int isFraudAction)
    {
        if (nodesToRender.Count != originalNodesData.Count) return;

        for (int i = 0; i < originalNodesData.Count; i++)
        {
            LocalNode meta = originalNodesData[i];
            GPUComputeNode gpuNode = nodesToRender[i];

            // Si Streamlit demande d'isoler/marquer un cluster spécifique
            if (targetCluster != -1 && meta.cluster_label == targetCluster)
            {
                if (isFraudAction == 1)
                {
                    gpuNode.color = new Vector4(1f, 0f, 0f, 1f); // Forçage Rouge Critique
                }
                else
                {
                    gpuNode.color = new Vector4(1f, 0.7f, 0f, 1f); // Orange d'alerte standard
                }
            }
            else // Réinitialisation automatique aux couleurs par défaut d'origine
            {
                if (meta.is_fraud_node == 1 || meta.risk_level == "critique")
                {
                    gpuNode.color = new Vector4(1f, 0f, 0f, 1f);
                }
                else
                {
                    switch (meta.cluster_label)
                    {
                        case 1: gpuNode.color = new Vector4(0f, 0.5f, 1f, 1f); break;
                        case 2: gpuNode.color = new Vector4(0.1f, 1f, 0.2f, 1f); break;
                        default: gpuNode.color = new Vector4(0.8f, 0.8f, 0.8f, 1f); break;
                    }
                }
            }
            nodesToRender[i] = gpuNode;
        }

        // Envoi direct et immédiat du nouveau tableau de données mis à jour à la carte graphique
        meshPropertiesBuffer.SetData(nodesToRender.ToArray());
    }

    void SpawnLine(Vector3 start, Vector3 end)
    {
        if (linePrefab == null) return;
        GameObject lineInstance = Instantiate(linePrefab, transform);
        LineRenderer lr = lineInstance.GetComponent<LineRenderer>();
        if (lr != null)
        {
            lr.positionCount = 2;
            lr.SetPosition(0, start);
            lr.SetPosition(1, end);
        }
    }

    void InitializeGPUBuffers()
    {
        meshPropertiesBuffer = new GraphicsBuffer(GraphicsBuffer.Target.Structured, nodesToRender.Count, Marshal.SizeOf(typeof(GPUComputeNode)));
        meshPropertiesBuffer.SetData(nodesToRender.ToArray());

        renderBounds = new Bounds(Vector3.zero, Vector3.one * 500000f);

        uint[] commandArgs = new uint[5] { (uint)nodeMesh.GetIndexCount(0), (uint)nodesToRender.Count, 0, 0, 0 };
        commandBuffer = new GraphicsBuffer(GraphicsBuffer.Target.IndirectArguments, 1, sizeof(uint) * 5);
        commandBuffer.SetData(commandArgs);

        dotsMaterial.SetBuffer("_NodesBuffer", meshPropertiesBuffer);
        isDataReady = true;
    }

    void Update()
    {
        if (!isDataReady) return;
        dotsMaterial.SetBuffer("_NodesBuffer", meshPropertiesBuffer);
        Graphics.DrawMeshInstancedIndirect(nodeMesh, 0, dotsMaterial, renderBounds, commandBuffer);
    }

    void OnDestroy()
    {
        meshPropertiesBuffer?.Release();
        commandBuffer?.Release();
    }
}