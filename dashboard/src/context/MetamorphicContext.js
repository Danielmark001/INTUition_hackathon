import React, { createContext, useContext, useState, useEffect } from "react";

// Create context
const MetamorphicContext = createContext(null);

// Provider component
export const MetamorphicProvider = ({ children }) => {
  const [systemState, setSystemState] = useState(null);
  const [services, setServices] = useState([]);
  const [transformations, setTransformations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch system data from Metamorphosis Engine
        const response = await fetch("/api/dashboard-data");
        const data = await response.json();

        setSystemState(data.current_state);
        setServices(Object.values(data.current_state?.services || {}));
        setTransformations(data.transformation_stats?.recent || []);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Set up refresh interval
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, []);

  // Provide context value
  const value = {
    systemState,
    services,
    transformations,
    loading,
    refresh: async () => {
      // Function to manually refresh data
      /* Implementation */
    },
  };

  return (
    <MetamorphicContext.Provider value={value}>
      {children}
    </MetamorphicContext.Provider>
  );
};

// Custom hook for using the context
export const useMetamorphic = () => {
  const context = useContext(MetamorphicContext);
  if (context === null) {
    throw new Error("useMetamorphic must be used within a MetamorphicProvider");
  }
  return context;
};
