import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE =
  "https://breathe-esg-platform-yv8f.onrender.com";

function App() {
  const [records, setRecords] = useState([]);
  const [failedRows, setFailedRows] = useState([]);
  const [sourceType, setSourceType] = useState("SAP");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const fetchRecords = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/api/records/`
      );

      setRecords(response.data);
    } catch (error) {
      console.error(error);
      setMessage("Failed to load records.");
    }
  };

  const fetchFailedRows = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/api/raw-records/failed/`
      );

      setFailedRows(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchFailedRows();
  }, []);

  const uploadToEndpoint = async (file) => {
    const formData = new FormData();

    formData.append("uploaded_file", file);
    formData.append("uploaded_by", "Yuvraaj");

    const endpointMap = {
      SAP: "sap",
      UTILITY: "utility",
      TRAVEL: "travel",
    };

    const endpoint = endpointMap[sourceType];

    return axios.post(
      `${API_BASE}/api/upload/${endpoint}/`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];

    if (!file) return;

    try {
      setUploading(true);
      setMessage("Uploading file...");

      await uploadToEndpoint(file);

      await fetchRecords();
      await fetchFailedRows();

      setMessage(
        `${sourceType} file uploaded successfully.`
      );
    } catch (error) {
      console.error(error);

      if (error.response?.data) {
        setMessage(
          JSON.stringify(error.response.data)
        );
      } else {
        setMessage(
          "Upload failed. Backend may still be waking up."
        );
      }
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const approveRecord = async (id) => {
    try {
      await axios.patch(
        `${API_BASE}/api/records/${id}/approve/`,
        {
          changed_by: "Yuvraaj",
        }
      );

      await fetchRecords();
    } catch (error) {
      console.error(error);
      setMessage("Approve failed.");
    }
  };

  const rejectRecord = async (id) => {
    try {
      await axios.patch(
        `${API_BASE}/api/records/${id}/reject/`,
        {
          changed_by: "Yuvraaj",
        }
      );

      await fetchRecords();
    } catch (error) {
      console.error(error);
      setMessage("Reject failed.");
    }
  };

  const approvedCount = records.filter(
    (r) => r.review_status === "APPROVED"
  ).length;

  const pendingCount = records.filter(
    (r) => r.review_status === "PENDING"
  ).length;

  const suspiciousCount = records.filter(
    (r) => r.suspicious_flag === true
  ).length;

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f4f4f5",
        padding: "24px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "1600px",
          margin: "0 auto",
        }}
      >
        <h1
          style={{
            fontSize: "56px",
            fontWeight: "800",
            marginBottom: "28px",
          }}
        >
          Breathe ESG Dashboard
        </h1>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
            marginBottom: "24px",
          }}
        >
          <StatCard
            title="Total Records"
            value={records.length}
          />

          <StatCard
            title="Approved"
            value={approvedCount}
            tone="green"
          />

          <StatCard
            title="Pending"
            value={pendingCount}
            tone="amber"
          />

          <StatCard
            title="Suspicious"
            value={suspiciousCount}
            tone="red"
          />

          <StatCard
            title="Failed Rows"
            value={failedRows.length}
            tone="slate"
          />
        </div>

        <div
          style={{
            backgroundColor: "white",
            borderRadius: "22px",
            padding: "28px",
            boxShadow:
              "0 2px 18px rgba(0,0,0,0.08)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "20px",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <h2
              style={{
                fontSize: "30px",
                fontWeight: "800",
                margin: 0,
              }}
            >
              Emission Records
            </h2>

            <div
              style={{
                display: "flex",
                gap: "12px",
                alignItems: "center",
              }}
            >
              <select
                value={sourceType}
                onChange={(e) =>
                  setSourceType(e.target.value)
                }
                style={{
                  padding: "12px",
                  borderRadius: "10px",
                  border: "1px solid #ccc",
                }}
              >
                <option value="SAP">SAP</option>
                <option value="UTILITY">
                  UTILITY
                </option>
                <option value="TRAVEL">
                  TRAVEL
                </option>
              </select>

              <label
                style={{
                  backgroundColor: "black",
                  color: "white",
                  padding: "12px 18px",
                  borderRadius: "12px",
                  cursor: "pointer",
                  fontWeight: "700",
                }}
              >
                {uploading
                  ? "Uploading..."
                  : "Upload CSV"}

                <input
                  type="file"
                  accept=".csv"
                  hidden
                  onChange={handleFileUpload}
                />
              </label>
            </div>
          </div>

          {message && (
            <div
              style={{
                marginBottom: "16px",
                padding: "12px",
                borderRadius: "10px",
                backgroundColor: "#eef2ff",
                color: "#3730a3",
                fontWeight: "600",
              }}
            >
              {message}
            </div>
          )}

          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr>
                  <Th>ID</Th>
                  <Th>Scope</Th>
                  <Th>Category</Th>
                  <Th>Quantity</Th>
                  <Th>Unit</Th>
                  <Th>Status</Th>
                  <Th>Risk</Th>
                  <Th>Actions</Th>
                </tr>
              </thead>

              <tbody>
                {records.map((record) => (
                  <tr
                    key={record.id}
                    style={{
                      backgroundColor:
                        record.suspicious_flag
                          ? "#fff1f2"
                          : "white",
                    }}
                  >
                    <Td>{record.id}</Td>
                    <Td>{record.scope}</Td>
                    <Td>{record.category}</Td>
                    <Td>{record.quantity}</Td>
                    <Td>
                      {record.normalized_unit}
                    </Td>

                    <Td>
                      <StatusPill
                        status={
                          record.review_status
                        }
                      />
                    </Td>

                    <Td>
                      {record.suspicious_flag
                        ? "⚠ Suspicious"
                        : "✓ Normal"}
                    </Td>

                    <Td>
                      <div
                        style={{
                          display: "flex",
                          gap: "10px",
                        }}
                      >
                        <button
                          style={buttonStyle(
                            "#22c55e"
                          )}
                          onClick={() =>
                            approveRecord(
                              record.id
                            )
                          }
                        >
                          Approve
                        </button>

                        <button
                          style={buttonStyle(
                            "#ef4444"
                          )}
                          onClick={() =>
                            rejectRecord(
                              record.id
                            )
                          }
                        >
                          Reject
                        </button>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div
          style={{
            backgroundColor: "white",
            borderRadius: "22px",
            padding: "28px",
            marginTop: "24px",
            boxShadow:
              "0 2px 18px rgba(0,0,0,0.08)",
          }}
        >
          <h2
            style={{
              fontSize: "28px",
              fontWeight: "800",
              marginBottom: "18px",
            }}
          >
            Failed Rows
          </h2>

          {failedRows.length === 0 ? (
            <div style={{ color: "#6b7280" }}>
              No failed rows yet.
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                }}
              >
                <thead>
                  <tr>
                    <Th>ID</Th>
                    <Th>Status</Th>
                    <Th>Error</Th>
                  </tr>
                </thead>

                <tbody>
                  {failedRows.map((row) => (
                    <tr key={row.id}>
                      <Td>{row.id}</Td>
                      <Td>
                        {row.processing_status}
                      </Td>
                      <Td>
                        {row.error_message ||
                          "—"}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  tone = "default",
}) {
  const tones = {
    default: {
      bg: "#ffffff",
      color: "#111827",
    },

    green: {
      bg: "#ecfdf5",
      color: "#065f46",
    },

    amber: {
      bg: "#fffbeb",
      color: "#92400e",
    },

    red: {
      bg: "#fef2f2",
      color: "#991b1b",
    },

    slate: {
      bg: "#f8fafc",
      color: "#0f172a",
    },
  };

  const style = tones[tone];

  return (
    <div
      style={{
        backgroundColor: style.bg,
        borderRadius: "18px",
        padding: "18px",
      }}
    >
      <div
        style={{
          color: "#64748b",
          fontSize: "14px",
          fontWeight: "700",
        }}
      >
        {title}
      </div>

      <div
        style={{
          color: style.color,
          fontSize: "34px",
          fontWeight: "800",
          marginTop: "6px",
        }}
      >
        {value}
      </div>
    </div>
  );
}

function StatusPill({ status }) {
  const map = {
    APPROVED: {
      bg: "#d1fae5",
      color: "#065f46",
    },

    REJECTED: {
      bg: "#fee2e2",
      color: "#991b1b",
    },

    PENDING: {
      bg: "#fef3c7",
      color: "#92400e",
    },
  };

  const s = map[status] || map.PENDING;

  return (
    <span
      style={{
        backgroundColor: s.bg,
        color: s.color,
        padding: "8px 14px",
        borderRadius: "999px",
        fontWeight: "800",
        fontSize: "13px",
      }}
    >
      {status}
    </span>
  );
}

function Th({ children }) {
  return (
    <th
      style={{
        textAlign: "left",
        padding: "16px",
      }}
    >
      {children}
    </th>
  );
}

function Td({ children }) {
  return (
    <td
      style={{
        padding: "16px",
      }}
    >
      {children}
    </td>
  );
}

function buttonStyle(bg) {
  return {
    backgroundColor: bg,
    color: "white",
    border: "none",
    padding: "10px 16px",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "700",
  };
}

export default App;