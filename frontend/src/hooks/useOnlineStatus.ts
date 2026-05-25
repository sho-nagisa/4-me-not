import { useEffect, useState } from "react";

const getOnlineStatus = () => {
  if (typeof navigator === "undefined") {
    return true;
  }

  return navigator.onLine;
};

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(getOnlineStatus);

  useEffect(() => {
    const updateOnlineStatus = () => setIsOnline(getOnlineStatus());

    window.addEventListener("online", updateOnlineStatus);
    window.addEventListener("offline", updateOnlineStatus);
    updateOnlineStatus();

    return () => {
      window.removeEventListener("online", updateOnlineStatus);
      window.removeEventListener("offline", updateOnlineStatus);
    };
  }, []);

  return isOnline;
}
