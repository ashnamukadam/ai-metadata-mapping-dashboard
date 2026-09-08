import api from "./api";

export const extractMetadata = async (connectionData) => {
  const token = localStorage.getItem("token");

  const payload = {
    database_type: connectionData.databaseType,
    host: connectionData.host,
    port: Number(connectionData.port),
    database_name: connectionData.databaseName,
    username: connectionData.username,
    password: connectionData.password,
  };

  console.log("Sending metadata payload:", payload);

  const response = await api.post(
    "/database/metadata",
    payload,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};